import asyncio
import json
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index.html"

rooms_lock = asyncio.Lock()
rooms: Dict[str, Dict[str, Any]] = {}

MAX_ROOMS = 1000
MIN_NUMBER = 1
MAX_NUMBER = 1_000_000


def _new_room_id() -> str:
    return secrets.token_urlsafe(4)


async def _safe_send(ws: WebSocket, message: Dict[str, Any]) -> None:
    try:
        await ws.send_json(message)
    except Exception:
        # Connection might already be closed; ignore.
        pass


def _require_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(INDEX_PATH.read_text(encoding="utf-8"))


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    role = None
    room_id = None

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _safe_send(ws, {"type": "error", "message": "Invalid JSON."})
                continue

            if not isinstance(msg, dict) or "type" not in msg:
                await _safe_send(ws, {"type": "error", "message": "Missing message type."})
                continue

            msg_type = msg.get("type")

            if role is None:
                if msg_type == "create_room":
                    async with rooms_lock:
                        if len(rooms) >= MAX_ROOMS:
                            await _safe_send(ws, {"type": "error", "message": "Room limit reached."})
                            continue
                        room_id = _new_room_id()
                        rooms[room_id] = {
                            "host": ws,
                            "joiner": None,
                            "secret": None,
                            "guesses": 0,
                        }
                    role = "host"
                    await _safe_send(ws, {"type": "room_created", "room_id": room_id})
                    continue

                if msg_type == "join_room":
                    room_id = msg.get("room_id")
                    if not isinstance(room_id, str) or not room_id:
                        await _safe_send(ws, {"type": "error", "message": "Invalid room ID."})
                        continue
                    async with rooms_lock:
                        room = rooms.get(room_id)
                        if not room:
                            await _safe_send(ws, {"type": "error", "message": "Room not found."})
                            continue
                        if room["joiner"] is not None:
                            await _safe_send(ws, {"type": "error", "message": "Room already has a joiner."})
                            continue
                        room["joiner"] = ws
                    role = "joiner"
                    await _safe_send(ws, {"type": "room_joined", "room_id": room_id, "role": "joiner"})
                    await _safe_send(rooms[room_id]["host"], {"type": "status", "message": "Joiner connected."})
                    continue

                await _safe_send(ws, {"type": "error", "message": "First message must be create_room or join_room."})
                continue

            if role == "host":
                if msg_type == "set_secret":
                    secret = _require_int(msg.get("secret"))
                    if secret is None or secret < MIN_NUMBER or secret > MAX_NUMBER:
                        await _safe_send(
                            ws,
                            {
                                "type": "error",
                                "message": f"Secret must be an integer between {MIN_NUMBER} and {MAX_NUMBER}.",
                            },
                        )
                        continue
                    async with rooms_lock:
                        if room_id not in rooms:
                            await _safe_send(ws, {"type": "error", "message": "Room no longer exists."})
                            continue
                        rooms[room_id]["secret"] = secret
                        rooms[room_id]["guesses"] = 0
                    await _safe_send(ws, {"type": "status", "message": "Secret set. Waiting for guesses."})
                    continue

                await _safe_send(ws, {"type": "error", "message": "Host can only set_secret."})
                continue

            if role == "joiner":
                if msg_type == "guess":
                    guess = _require_int(msg.get("guess"))
                    if guess is None or guess < MIN_NUMBER or guess > MAX_NUMBER:
                        await _safe_send(
                            ws,
                            {
                                "type": "error",
                                "message": f"Guess must be an integer between {MIN_NUMBER} and {MAX_NUMBER}.",
                            },
                        )
                        continue
                    async with rooms_lock:
                        room = rooms.get(room_id)
                        if not room:
                            await _safe_send(ws, {"type": "error", "message": "Room no longer exists."})
                            continue
                        if room["secret"] is None:
                            await _safe_send(ws, {"type": "error", "message": "Host has not set a secret yet."})
                            continue
                        room["guesses"] += 1
                        secret = room["secret"]
                        guesses = room["guesses"]
                    if guess < secret:
                        result = "higher"
                    elif guess > secret:
                        result = "lower"
                    else:
                        result = "correct"
                    await _safe_send(ws, {"type": "guess_result", "result": result, "guesses": guesses})
                    if result == "correct":
                        await _safe_send(
                            rooms[room_id]["host"],
                            {"type": "status", "message": f"Joiner guessed correctly in {guesses} tries."},
                        )
                    continue

                await _safe_send(ws, {"type": "error", "message": "Joiner can only guess."})
                continue

    except WebSocketDisconnect:
        pass
    finally:
        if role and room_id:
            async with rooms_lock:
                room = rooms.get(room_id)
                if room:
                    other = None
                    if role == "host":
                        room["host"] = None
                        other = room.get("joiner")
                    else:
                        room["joiner"] = None
                        other = room.get("host")
                    if other is not None:
                        await _safe_send(other, {"type": "status", "message": "Other player disconnected."})
                    if room.get("host") is None and room.get("joiner") is None:
                        rooms.pop(room_id, None)
