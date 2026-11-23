# Online Chess setup

Online Chess uses a small Python WebSocket server. The game page can remain on
its existing static host; the WebSocket server must run separately on a host
that supports persistent WebSocket connections.

## Run locally

Install the server dependencies once:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In one terminal, serve Game Center:

```powershell
.\.venv\Scripts\python.exe scores_server.py
```

In another terminal, run the online game server:

```powershell
.\.venv\Scripts\python.exe online_chess_server.py
```

Open `http://localhost:8000`, choose Chess, select **Online 2-player**, then
create a room. Share its room code with the other player. The server listens
on port `8766` by default and validates every move before broadcasting it.
The default allowed website origins are `http://localhost:8000` and
`http://127.0.0.1:8000`.

## Host online

Deploy `online_chess_server.py` on a service that supports WebSockets and
provides a public `wss://` endpoint. Install `requirements.txt` and start it
with `python online_chess_server.py`. Configure:

- `ALLOWED_ORIGINS`: comma-separated, exact origin(s) of the Game Center site,
  such as `https://example.com` (no path or trailing slash).
- `PORT`: set automatically by many hosting services; defaults to `8766`.
- `HOST`: defaults to `0.0.0.0`.

For Render, connect this repository as a Blueprint and use the included
`render.yaml`. Render will ask for `ALLOWED_ORIGINS`; enter the exact origin
of the existing Game Center website. After deployment, copy the service
hostname from Render and use it in the meta tag below.

Set the `chess-websocket-url` meta tag in `index.html` to the hosted endpoint,
for example:

```html
<meta name="chess-websocket-url" content="wss://your-service.example/ws">
```

If that tag is empty, the page connects to `ws(s)://<page-host>:8766`.
Use HTTPS and `wss://` for a public website. Do not configure permissive
origins such as `*`.

Rooms and games are kept in server memory: they are lost when the service
restarts, and this single-process server should not be scaled to multiple
instances without adding shared room storage and coordination.
