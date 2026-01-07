# TEST_online_game
Minimal two-player number guessing game (FastAPI + WebSockets).

## How to join as the second player
1) Open the site in a second browser tab or a different device.
2) Enter the Room ID shown by the host.
3) Click "Join room".
4) Enter guesses and click "Send guess".

## Walkthrough (local)
1) Install dependencies:
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```
2) Run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
3) Open `http://localhost:8000` in two tabs:
   - Tab A: click "Create room", copy the Room ID, set the secret.
   - Tab B: paste the Room ID, click "Join room", then start guessing.

## Walkthrough (local + phone on same Wi-Fi)
1) Run the server with `--host 0.0.0.0` (already shown above).
2) Find your computer's local IP address (example: `192.168.1.50`).
3) From your phone on the same Wi-Fi, open:
```
http://YOUR_IP:8000
```
4) Use one device as host and the other as joiner.

If the phone cannot connect, allow Python/Uvicorn through your firewall or try a different port.

## Walkthrough (Render.com)
1) Push this repo to GitHub (Render pulls from a Git repo).
2) In Render, click "New +" → "Web Service" → connect your GitHub repo.
3) Fill in:
   - Name: any name
   - Region: choose closest
   - Runtime: Python
   - Build Command:
```bash
pip install -r requirements.txt
```
4) Start Command:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
5) Click "Create Web Service" and wait for the deploy to finish.
6) Open the public Render URL on any device (phone works off Wi-Fi).
7) Use one device as host and the other as joiner.

If you are stuck, the two most common issues are:
- Repo not connected or not pushed to GitHub yet.
- Start command missing `$PORT` (Render requires it).
