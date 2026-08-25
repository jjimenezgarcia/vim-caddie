"""WebSocket bridge between the browser (xterm.js) and a sandboxed, real
Neovim session running in a locked-down, single-use Docker container — one
per exercise (see exercises/*.json and server/exercises.py).

Several things are multiplexed over one WebSocket connection, as JSON frames:

  - {"type": "term", "data": <base64>}       server -> client, raw PTY
    bytes so xterm.js renders the *real* Neovim TUI, verbatim.
    {"type": "input", "data": <str>}         client -> server, raw
    keystrokes written straight into the pty. Neither side interprets
    Vim commands here — Neovim does all of that.
  - {"type": "keypress", "data": <str>}      client -> server only, one
    real physical key press (xterm.js's onKey, not onData — see
    VimTerminal.jsx — onData also carries the terminal's own automatic
    protocol replies, which aren't the player typing). Drives "hit" below.
  - {"type": "state", "lines": [...], "cursor": [row, col], "mode": "n"}
    server -> client only, read via Neovim's own RPC socket
    (nvim_get_mode / nvim_win_get_cursor / nvim_buf_get_lines). Feeds
    _check_success, checked backend-side — never inside the sandbox.
  - {"type": "hit", "good": bool, "index": N, "total": M}   server ->
    client, one per keystroke, for exercises with a fixed
    ideal_keystrokes reference path: does it match at the current
    position? A mismatch doesn't reset position, it just doesn't advance it.
  - {"type": "progress", "reached": N, "count": M}   server -> client,
    for a reach_markers exercise instead (see _check_reach_markers) — no
    fixed path to score keystrokes against, just "how many targets so far".
  - {"type": "holed"}   server -> client, sent once _check_success's
    configured checker (buffer_match / cursor_at / reach_markers) is
    satisfied.

See nvim_session.py's NvimSession for what actually owns a session's
sandboxed docker+nvim process; this module is just the WebSocket/HTTP
front door to it.
"""

import asyncio
import json
import logging
import os
import urllib.parse

import websockets
from websockets.datastructures import Headers
from websockets.http11 import Response

import auth as auth_mod
import exercises as exercises_mod
import progress as progress_mod
from nvim_session import DEFAULT_COLS, DEFAULT_ROWS, NvimSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("vim-caddie")

HOST = os.environ.get("VIM_CADDIE_HOST", "127.0.0.1")
PORT = int(os.environ.get("VIM_CADDIE_PORT", "8765"))
DEFAULT_EXERCISE = os.environ.get("VIM_CADDIE_DEFAULT_EXERCISE", "fix-the-typo")


def _json_response(payload, status=200, reason="OK"):
    body = json.dumps(payload).encode("utf-8")
    headers = Headers(
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
            # local dev only — frontend (5173) and backend (8765) are
            # different origins
            ("Access-Control-Allow-Origin", "*"),
        ]
    )
    return Response(status, reason, headers, body)


def _preflight_response():
    headers = Headers(
        [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "X-Username, X-Password, Authorization"),
            ("Access-Control-Max-Age", "600"),
            ("Content-Length", "0"),
        ]
    )
    return Response(204, "No Content", headers, b"")


def _bearer_token(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[len("bearer "):].strip()
    return ""


async def process_request(connection, request):
    """Handles plain HTTP GET/POST /api/exercises, /api/signup, /api/login,
    /api/progress on the same port, and stashes the requested exercise id
    + session token onto the connection for handler() to pick up —
    sidesteps needing to know exactly which attribute this websockets
    version exposes the request path under inside handler() itself.
    """
    if request.method == "OPTIONS":
        return _preflight_response()

    path = request.path
    parsed = urllib.parse.urlsplit(path)
    query = urllib.parse.parse_qs(parsed.query)

    if parsed.path == "/api/exercises":
        return _json_response(exercises_mod.list_exercises())

    if parsed.path in ("/api/signup", "/api/login"):
        username = request.headers.get("X-Username", "")
        password = request.headers.get("X-Password", "")
        try:
            if parsed.path == "/api/signup":
                token, resolved_username = auth_mod.sign_up(username, password)
            else:
                token, resolved_username = auth_mod.log_in(username, password)
        except auth_mod.AuthError as e:
            status = 401 if parsed.path == "/api/login" else 400
            return _json_response({"error": str(e)}, status=status, reason="Error")
        return _json_response({"token": token, "username": resolved_username})

    if parsed.path == "/api/logout":
        auth_mod.log_out(_bearer_token(request))
        return _json_response({"ok": True})

    if parsed.path == "/api/progress":
        username = auth_mod.username_for_token(_bearer_token(request))
        if username is None:
            return _json_response({"error": "not signed in"}, status=401, reason="Unauthorized")
        return _json_response(progress_mod.get_progress(username))

    # Everything else is the WS game connection's handshake — kept on its
    # own path (not "/") so a reverse proxy can route by path alone,
    # without inspecting Upgrade headers to tell it apart from the SPA's
    # own "/".
    if parsed.path != "/ws":
        return _json_response({"error": "not found"}, status=404, reason="Not Found")

    exercise_id = query.get("exercise", [DEFAULT_EXERCISE])[0]
    connection._vc_exercise_id = exercise_id  # noqa: SLF001 — our own stash
    # Requested subprotocols arrive as a comma-separated header at this
    # point in the handshake; the client only ever sends the one token
    # value (see src/useNvimSession.js), so the first is the whole answer.
    requested = request.headers.get("Sec-WebSocket-Protocol", "")
    connection._vc_token = requested.split(",")[0].strip()  # noqa: SLF001
    return None  # continue the WS handshake


async def handler(websocket, *_compat_args):
    loop = asyncio.get_running_loop()
    exercise_id = getattr(websocket, "_vc_exercise_id", DEFAULT_EXERCISE)
    token = getattr(websocket, "_vc_token", "")
    username = auth_mod.username_for_token(token)
    try:
        exercise = exercises_mod.load_exercise(exercise_id)
    except FileNotFoundError as e:
        log.warning("rejecting connection: %s", e)
        await websocket.close(code=1008, reason=str(e))
        return

    session = NvimSession(loop, websocket, exercise, username=username)
    log.info(
        "session %s: starting exercise=%s image=%s for %s",
        session.session_id, exercise_id, exercise["image"], websocket.remote_address,
    )
    try:
        try:
            await session.start_pty()
        except (OSError, RuntimeError) as e:
            log.error("session %s: launcher did not start the sandbox: %s", session.session_id, e)
            await websocket.close(code=1011, reason="could not start sandbox")
            return
        session.start_rpc()
        session.start_watchdog()
        # Only success.type ever reaches the client here — the frontend
        # uses it purely to pick which UI to render (reach_markers'
        # progress strip vs. the par/hits strip; see ExercisePanel.jsx),
        # never the target content itself.
        await session._safe_send({"type": "ready", "exercise": {
            "id": exercise["id"], "title": exercise["title"],
            "description": exercise["description"], "par": exercise.get("par"),
            "success": {"type": exercise.get("success", {}).get("type")},
        }})
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            kind = msg.get("type")
            if kind == "input":
                session.write_input(msg.get("data", ""))
            elif kind == "keypress":
                session.score_keypress(msg.get("data", ""))
            elif kind == "resize":
                cols = int(msg.get("cols", DEFAULT_COLS))
                rows = int(msg.get("rows", DEFAULT_ROWS))
                session.resize(cols, rows)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        session.close()


def _select_subprotocol(connection, subprotocols):
    """The client's session token (see process_request's docstring on why
    it travels this way) arrives here as the requested subprotocol —
    echoing it back is what makes this a normal, spec-compliant
    negotiation instead of a value the client sent into the void."""
    return subprotocols[0] if subprotocols else None


async def main():
    async with websockets.serve(
        handler,
        HOST,
        PORT,
        max_size=2**20,
        process_request=process_request,
        select_subprotocol=_select_subprotocol,
    ):
        log.info("vim-caddie backend listening on ws://%s:%s", HOST, PORT)
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
