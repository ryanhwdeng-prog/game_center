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

## Play on the same Wi-Fi network

On the host computer, find its Wi-Fi IPv4 address with `ipconfig` (for example,
`192.168.68.133`). Start `scores_server.py` as usual, then start the WebSocket
server with that address included in its allowed origins:

```powershell
$env:ALLOWED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000,http://192.168.68.133:8000"
.\.venv\Scripts\python.exe online_chess_server.py
```

Replace the example address with the host computer's current IPv4 address.
On the other device, open `http://192.168.68.133:8000`, choose Chess, select
**Online 2-player**, and join using the room code. The page uses that same
address for its WebSocket connection on port `8766`.

If another device cannot open the page, allow inbound TCP ports `8000` and
`8766` through Windows Firewall on the **Private** profile only, and mark the
Wi-Fi network Private only if it is trusted. Guest Wi-Fi and access-point
isolation can also prevent devices from reaching each other. The host's
address may change when its router renews DHCP.

## Host online

Deploy `online_chess_server.py` on a service that supports WebSockets and
provides a public `wss://` endpoint. Install `requirements.txt` and start it
with `python online_chess_server.py`. Configure:

- `ALLOWED_ORIGINS`: comma-separated, exact origin(s) of the Game Center site,
  such as `https://example.com` (no path or trailing slash).
- `PORT`: set automatically by many hosting services; defaults to `8766`.
- `HOST`: defaults to `0.0.0.0`.

For Render, connect this repository as a Blueprint and use the included
`render.yaml`, which explicitly selects the Free compute plan. Render will
ask for `ALLOWED_ORIGINS`; enter the exact origin of the existing Game Center
website. After deployment, copy the service hostname from Render and use it
in the meta tag below. Check the selected plan and account usage in Render
before confirming deployment.

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
