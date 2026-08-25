"""One player's sandboxed nvim session and its two channels: a pty (raw
terminal bytes, for xterm.js) and a Neovim RPC socket (read-only from our
side, drives success-checking). See app.py's module docstring for the
WebSocket message protocol this feeds.

This process never touches docker.sock or spawns containers directly —
launcher.py is the only thing in this stack with docker.sock mounted (see
docker-compose.yml and launcher.py's module docstring for why). This
class creates the session's workspace on disk, then asks the launcher
(over the internal `docker-control` network) to start a sandboxed
container for it; the pty byte stream is relayed over that same
connection. init.vim and the exercise's workspace files are generated per
session (server/vimrc.py) and written into the bind-mounted /state dir,
not baked into the sandbox image.
"""

import asyncio
import base64
import json
import logging
import os
import random
import shutil
import subprocess
import tempfile
import threading
import time
import uuid

import pynvim
import websockets

import progress as progress_mod
import vimrc

log = logging.getLogger("vim-caddie")

SOCKET_WAIT_TIMEOUT = 5.0
DEFAULT_COLS, DEFAULT_ROWS = 80, 24

LAUNCHER_HOST = os.environ.get("VIM_CADDIE_LAUNCHER_HOST", "launcher")
LAUNCHER_PORT = int(os.environ.get("VIM_CADDIE_LAUNCHER_PORT", "9000"))
LAUNCHER_CONNECT_RETRIES = 10
LAUNCHER_CONNECT_DELAY = 0.3

# /state is a writable host bind mount with no docker-side size limit (see
# launcher.py's _docker_run_cmd) — nvim.sock is ~0 bytes, so growth past
# this is writefile()-abuse, not legitimate use.
SESSION_DIR_MAX_BYTES = 1_000_000
SESSION_DIR_CHECK_INTERVAL = 3.0

# Must match `useradd --uid` in docker/nvim-sandbox/Dockerfile — exists
# only inside the sandbox image, owns nothing on the host, used for
# nothing except running this one nvim process.
SANDBOX_UID = 10001

SESSIONS_ROOT = os.environ.get(
    "VIM_CADDIE_SESSIONS_DIR", os.path.join(os.path.expanduser("~"), ".cache", "vim-caddie", "sessions")
)
os.makedirs(SESSIONS_ROOT, exist_ok=True)


class NvimSession:
    """Owns one sandboxed docker+nvim process and its two channels."""

    def __init__(self, loop, websocket, exercise, username=None):
        self.loop = loop
        self.ws = websocket
        self.exercise = exercise
        # Resolved from a verified session token (auth.py)
        self.username = username
        self.par = exercise.get("par")
        # Empty for reach_markers AND for professional/genius.
        self.ideal_keystrokes = exercise.get("ideal_keystrokes", "")
        self.expected_index = 0
        self.total_keystrokes = 0
        self.holed = False
        self.session_id = uuid.uuid4().hex[:12]
        self.session_dir = tempfile.mkdtemp(prefix=f"{self.session_id}-", dir=SESSIONS_ROOT)
        # The access boundary is the directory (mkdtemp leaves it 0700),
        # not the socket's own permission bits. This ACL entry adds
        # exactly one more identity — `player` (SANDBOX_UID), the
        # container's dedicated, single-purpose user — rather than
        # running the container as this backend's own uid just to make
        # ownership line up.
        try:
            subprocess.run(
                ["setfacl", "-m", f"u:{SANDBOX_UID}:rwx", self.session_dir],
                check=True, capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            log.warning(
                "session %s: setfacl unavailable/failed, falling back to a "
                "world-writable session dir (0777) — less isolation than intended",
                self.session_id,
            )
            os.chmod(self.session_dir, 0o777)
        self.sock_path = os.path.join(self.session_dir, "nvim.sock")
        self._data_reader = None
        self._data_writer = None
        self.nvim = None
        self._rpc_thread = None
        self._watchdog_task = None
        self._closed = False
        self._markers_reached = 0
        self._marker_cell = None
        self._checking_markers = False

    # ---- pty / docker channel ------------------------------------------------
    def _seed_workspace(self):
        """Writes this exercise's init.vim + starting files into session_dir
        (bind-mounted at /state), generated per session rather than baked
        into the image — see vimrc.py's module docstring."""
        init_vim = vimrc.render_init_vim(self.exercise["permissions"]["commands"])
        with open(os.path.join(self.session_dir, "init.vim"), "w", encoding="utf-8") as f:
            f.write(init_vim)

        workspace_dir = os.path.join(self.session_dir, "workspace")
        os.makedirs(workspace_dir, exist_ok=True)
        workspace_root = os.path.realpath(workspace_dir)
        for rel_path, content in self.exercise["workspace"].items():
            full_path = os.path.realpath(os.path.join(workspace_dir, rel_path))
            if os.path.commonpath([full_path, workspace_root]) != workspace_root:
                log.warning(
                    "session %s: refusing to write workspace path outside workspace dir: %r",
                    self.session_id, rel_path,
                )
                continue
            os.makedirs(os.path.dirname(full_path) or workspace_dir, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    async def start_pty(self):
        """Asks launcher.py to actually spawn the sandbox container — this
        process has no docker.sock and never runs `docker` itself (see
        this module's docstring and launcher.py's). The connection opened
        here IS the container's pty: raw bytes both ways for the rest of
        the session, closing it is what tears the container down."""
        self._seed_workspace()
        reader, writer = await self._connect_launcher()
        request = {
            "op": "start",
            "session_id": self.session_id,
            "exercise_id": self.exercise["id"],
            "session_dir": self.session_dir,
            "cols": DEFAULT_COLS,
            "rows": DEFAULT_ROWS,
        }
        writer.write((json.dumps(request) + "\n").encode())
        await writer.drain()
        ack = json.loads(await reader.readline())
        if not ack.get("ok"):
            writer.close()
            raise RuntimeError(f"launcher refused to start session: {ack.get('error')}")
        self._data_reader = reader
        self._data_writer = writer
        self.loop.create_task(self._pty_read_loop())

    @staticmethod
    async def _connect_launcher():
        for attempt in range(LAUNCHER_CONNECT_RETRIES):
            try:
                return await asyncio.open_connection(LAUNCHER_HOST, LAUNCHER_PORT)
            except OSError:
                if attempt == LAUNCHER_CONNECT_RETRIES - 1:
                    raise
                await asyncio.sleep(LAUNCHER_CONNECT_DELAY)

    async def _pty_read_loop(self):
        try:
            while True:
                data = await self._data_reader.read(65536)
                if not data:
                    break
                payload = {"type": "term", "data": base64.b64encode(data).decode("ascii")}
                await self._safe_send(payload)
        except (OSError, ConnectionError):
            pass
        finally:
            # EOF means the launcher tore the container down, for any
            # reason (:q!/:wq!, a crash, the launcher connection dying) —
            # the one reliable "session is over" signal. Skipped if we're
            # already closing (close() closing this same connection would
            # otherwise trigger a second, redundant _handle_exit).
            if not self._closed:
                self.loop.create_task(self._handle_exit())

    async def _handle_exit(self):
        await self._safe_send({"type": "exit"})
        self.close()
        try:
            await self.ws.close(code=1000, reason="nvim session ended")
        except Exception:
            pass

    async def _safe_send(self, payload):
        if self._closed:
            return
        try:
            await self.ws.send(json.dumps(payload))
        except websockets.exceptions.ConnectionClosed:
            pass

    def write_input(self, data: str):
        """Raw bytes bound for the pty — everything Neovim needs to see,
        including xterm.js's own automatic protocol replies (cursor-
        position reports, OSC color queries, etc. that Neovim's startup
        and every redraw ask the terminal to answer). Those aren't the
        player typing, so this must NOT score — see score_keypress(),
        driven by a separate {"type":"keypress"} message the frontend
        only sends from term.onKey (real physical key presses)."""
        if self._data_writer is None:
            return
        try:
            self._data_writer.write(data.encode("utf-8"))
        except (OSError, RuntimeError):
            pass

    def score_keypress(self, data):
        """Counts every real keystroke toward total_keystrokes whenever
        there's a par to compare it against — reach_markers (no par) is
        the only case with nothing to count. Live per-keystroke hit/miss
        feedback is a *separate*, narrower gate: it needs the actual
        reference sequence (ideal_keystrokes), which professional/genius
        exercises deliberately don't have loaded here (see self.par's
        comment in __init__) — without it there's nothing to compare a
        keystroke against, so those tiers still get their final stroke
        count recorded, just no live "good"/"bad" signal that would
        otherwise leak the hidden solution one correct keystroke at a
        time."""
        if self.holed or self.par is None:
            return
        for ch in data:
            self.total_keystrokes += 1
            if not self.ideal_keystrokes:
                continue
            good = (
                self.expected_index < len(self.ideal_keystrokes)
                and ch == self.ideal_keystrokes[self.expected_index]
            )
            if good:
                self.expected_index += 1
            payload = {
                "type": "hit",
                "good": good,
                "index": self.expected_index,
                "total": len(self.ideal_keystrokes),
            }
            self.loop.create_task(self._safe_send(payload))

    def resize(self, cols, rows):
        """Fires off a short-lived control connection to launcher.py — the
        pty is on that side now, and the data connection (start_pty) is
        raw bytes with no room to carry an out-of-band signal like this."""
        if self._closed:
            return
        self.loop.create_task(self._send_resize(cols, rows))

    async def _send_resize(self, cols, rows):
        try:
            reader, writer = await asyncio.open_connection(LAUNCHER_HOST, LAUNCHER_PORT)
        except OSError:
            return
        try:
            request = {"op": "resize", "session_id": self.session_id, "cols": cols, "rows": rows}
            writer.write((json.dumps(request) + "\n").encode())
            await writer.drain()
            await reader.readline()
        except (OSError, ConnectionError):
            pass
        finally:
            writer.close()

    # ---- neovim RPC channel (read-only from our side) ------------------------
    def start_rpc(self):
        self._rpc_thread = threading.Thread(target=self._rpc_worker, daemon=True)
        self._rpc_thread.start()

    def _rpc_worker(self):
        deadline = time.monotonic() + SOCKET_WAIT_TIMEOUT
        while time.monotonic() < deadline and not self._closed:
            if os.path.exists(self.sock_path):
                break
            time.sleep(0.1)
        if self._closed or not os.path.exists(self.sock_path):
            log.warning("session %s: nvim RPC socket never appeared", self.session_id)
            return

        # The socket exists (--listen creates it) before init.vim finishes
        # sourcing and chmods it to something we can connect to (vimrc.py)
        # — nvim processes --listen before sourcing -u. Polling for
        # existence alone can land right in that gap, so retry the attach
        # itself too.
        nvim = None
        for attempt in range(10):
            if self._closed:
                return
            try:
                nvim = pynvim.attach("socket", path=self.sock_path)
                break
            except Exception:
                time.sleep(0.15)
        if nvim is None:
            log.error("session %s: failed to attach RPC client after retries", self.session_id)
            return
        self.nvim = nvim

        def push_state():
            try:
                lines = nvim.request("nvim_buf_get_lines", 0, 0, -1, False)
                cursor = nvim.request("nvim_win_get_cursor", 0)
                mode = nvim.request("nvim_get_mode")["mode"]
            except Exception:
                return
            payload = {"type": "state", "lines": lines, "cursor": cursor, "mode": mode}
            asyncio.run_coroutine_threadsafe(self._safe_send(payload), self.loop)
            self._check_success(nvim, lines, cursor)

        def on_notification(name, args):
            if name == "vim_caddie_state":
                push_state()

        try:
            # rpcnotify(0, ...) ("broadcast to every channel") only
            # reaches channels that called nvim_subscribe() for that
            # event name first — without this, on_notification never fires.
            nvim.subscribe("vim_caddie_state")
            # A reach_markers exercise needs its first target placed
            # before the player can do anything — same one-time-setup
            # spot as the baseline push_state() call right below.
            self._init_reach_markers(nvim)
            # The autocmd that broadcasts 'vim_caddie_state' on every
            # edit/cursor/mode change lives in init.vim itself (live from
            # nvim's first moment, not from this RPC handshake landing) —
            # here we just fetch one fresh baseline snapshot and listen.
            push_state()
            nvim.run_loop(None, on_notification)
        except (OSError, EOFError):
            # nvim quitting (:q!/:wq!/a crash) breaks this socket —
            # BrokenPipeError/ConnectionResetError are OSError subclasses
            # — at essentially the same moment pty EOF fires and
            # _handle_exit takes care of the session.
            log.info("session %s: RPC connection closed (nvim exited)", self.session_id)
        except Exception:
            if not self._closed:
                log.exception("session %s: RPC loop ended unexpectedly", self.session_id)

    # ---- /state disk-usage watchdog -------------------------------------------
    # docker's bind-mount flags have no noexec/size-limit option (unlike
    # --tmpfs), so this is the mitigation for a session dropping a large
    # payload on the one mount that has to stay writable.
    def start_watchdog(self):
        self._watchdog_task = self.loop.create_task(self._watchdog())

    async def _watchdog(self):
        while not self._closed:
            await asyncio.sleep(SESSION_DIR_CHECK_INTERVAL)
            if self._closed:
                return
            size = self._session_dir_size()
            if size > SESSION_DIR_MAX_BYTES:
                log.warning(
                    "session %s: /state grew to %d bytes (limit %d) — closing session",
                    self.session_id, size, SESSION_DIR_MAX_BYTES,
                )
                try:
                    await self.ws.close(code=1011, reason="session resource limit exceeded")
                except Exception:
                    pass
                self.close()
                return

    def _session_dir_size(self):
        total = 0
        for dirpath, _dirnames, filenames in os.walk(self.session_dir):
            for name in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, name))
                except OSError:
                    pass
        return total

    # ---- success check (trusted-side only, never inside the sandbox) --------
    def _check_success(self, nvim, lines, cursor):
        """Called from the RPC worker thread on every buffer/cursor/mode
        push. exercise["success"]["type"] is a discriminated union, so more
        checker types can be added later (e.g. filesystem_state) without a
        schema break — three implemented so far:

          - buffer_match: live buffer content == success.content
          - cursor_at: live cursor position == (success.line, success.col)
            — for pure-navigation exercises with no editing at all, where
            buffer_match could never fire since the text never changes.
            Coordinates are 1-indexed line AND 1-indexed col, matching how
            cursor_start is already authored (itself fed straight to
            Vimscript's `cursor(line, col)`, which is 1-indexed on both).
            nvim_win_get_cursor's own wire format is the odd one out here —
            1-indexed row but *0-indexed* col — so col gets +1'd below to
            compare apples to apples with what an exercise author writes.
          - reach_markers: generic "the cursor visits N configured target
            cells" — see _check_reach_markers. Unlike the other two, this
            one is a multi-step, side-effecting flow (clear a reached
            cell, maybe place a new one, maybe hole), not a single
            match-then-hole check, so it's split into its own method
            rather than squeezed into the shape below.
        """
        if self.holed:
            return
        success = self.exercise.get("success", {})
        kind = success.get("type")

        if kind == "reach_markers":
            self._check_reach_markers(nvim, cursor, success)
            return

        if kind == "buffer_match":
            actual = "\n".join(lines)
            expected = success.get("content", "").rstrip("\n")
            matched = actual == expected
        elif kind == "cursor_at":
            row, col0 = cursor
            matched = row == success.get("line") and (col0 + 1) == success.get("col")
        else:
            return

        if matched:
            self.holed = True
            strokes = self.total_keystrokes if self.par is not None else None
            progress_mod.record_hole_out(self.username, self.exercise["id"], strokes)
            asyncio.run_coroutine_threadsafe(self._safe_send({"type": "holed"}), self.loop)

    # ---- reach_markers: generic "cursor visits N target cells" ---------------
    def _init_reach_markers(self, nvim):
        success = self.exercise.get("success", {})
        if success.get("type") != "reach_markers":
            return
        self._markers_reached = 0
        self._checking_markers = True
        try:
            self._spawn_marker(nvim, success)
        finally:
            self._checking_markers = False

    def _spawn_marker(self, nvim, success):
        """Places one marker_char at a random empty_char cell, never on the
        player's current cursor cell. No-ops (silently) if the buffer has
        no empty cells left — a fixed-size grid with a sane count for that
        grid is on the exercise author, not something to engineer around."""
        try:
            lines = nvim.request("nvim_buf_get_lines", 0, 0, -1, False)
            cursor_row, cursor_col = nvim.request("nvim_win_get_cursor", 0)
        except Exception:
            return
        empty_char = success.get("empty_char", ".")
        cursor_cell = (cursor_row - 1, cursor_col)
        candidates = [
            (r, c)
            for r, line in enumerate(lines)
            for c, ch in enumerate(line)
            if ch == empty_char and (r, c) != cursor_cell
        ]
        if not candidates:
            return
        row, col = random.choice(candidates)
        marker_char = success.get("marker_char", "@")
        new_line = lines[row][:col] + marker_char + lines[row][col + 1 :]
        try:
            nvim.request("nvim_buf_set_lines", 0, row, row + 1, False, [new_line])
        except Exception:
            return
        self._marker_cell = (row, col)

    def _check_reach_markers(self, nvim, cursor, success):
        if self._checking_markers:
            return
        row1, col0 = cursor
        if (row1 - 1, col0) != self._marker_cell:
            return
        self._checking_markers = True
        try:
            # Reached: clear this cell, count it, tell the client, then
            # either place the next one or finish.
            try:
                lines = nvim.request("nvim_buf_get_lines", 0, 0, -1, False)
                r, c = self._marker_cell
                empty_char = success.get("empty_char", ".")
                cleared = lines[r][:c] + empty_char + lines[r][c + 1 :]
                nvim.request("nvim_buf_set_lines", 0, r, r + 1, False, [cleared])
            except Exception:
                return
            self._marker_cell = None
            self._markers_reached += 1
            count = success.get("count", 1)
            asyncio.run_coroutine_threadsafe(
                self._safe_send({"type": "progress", "reached": self._markers_reached, "count": count}),
                self.loop,
            )
            if self._markers_reached >= count:
                self.holed = True
                # No fixed reference path for a reach_markers exercise,
                # so no meaningful stroke count to compare across
                # attempts — just record that it's been holed at all.
                progress_mod.record_hole_out(self.username, self.exercise["id"], None)
                asyncio.run_coroutine_threadsafe(self._safe_send({"type": "holed"}), self.loop)
            elif success.get("respawn", True):
                self._spawn_marker(nvim, success)
        finally:
            self._checking_markers = False

    # ---- lifecycle -------------------------------------------------------------
    def close(self):
        if self._closed:
            return
        self._closed = True
        if self._watchdog_task is not None:
            self._watchdog_task.cancel()
        # Closing this is the actual "stop the container" signal —
        # launcher.py tears it down when it sees this connection end (see
        # its module docstring).
        if self._data_writer is not None:
            try:
                self._data_writer.close()
            except Exception:
                pass
        if self.nvim is not None:
            try:
                self.nvim.close()
            except Exception:
                pass
        shutil.rmtree(self.session_dir, ignore_errors=True)
        log.info("session %s: cleaned up", self.session_id)
