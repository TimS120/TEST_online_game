# TEST_online_game
Minimal two-player number guessing game (FastAPI + WebSockets).

## How to join as the second player
1) Open the invite link the host copied (it auto-joins).
2) Enter guesses and click "Send guess".

## Walkthrough (server start + Cloudflare Tunnel)
1) Download `cloudflared`:
   - Windows: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
2) Run your server locally:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
3) In a second terminal, start the tunnel:
```bash
cloudflared tunnel --url http://localhost:8000
```
4) `cloudflared` prints a public HTTPS URL (example: `https://random.trycloudflare.com`).
5) Open that URL on any device, create a room, and share the invite link with player two.

Notes:
- Keep the tunnel command running while others use the game.
- Anyone with the URL can access your server.