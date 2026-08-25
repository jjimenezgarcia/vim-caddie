"""The *only* thing in this stack with docker.sock mounted (see
docker-compose.yml). backend has none — it talks to this over the
internal `docker-control` network instead, with a protocol that has
exactly two operations: start a sandbox for a known exercise, resize its
pty. There is no operation that takes an arbitrary docker command, an
arbitrary image, or an arbitrary bind-mount source, so a full RCE in
backend (network-facing, runs untrusted player keystrokes through a real
Neovim) still doesn't get an attacker anything beyond one more sandboxed,
network-isolated container — the same thing a legitimate player already
gets. That's the property a generic "docker socket proxy" (endpoint
allowlisting) can't give you: it can restrict *which* Docker API calls a
client may make, but not what's inside a call's own body — a compromised
client can still ask an allowed "create container" call for
Privileged=true and a host bind mount. Here the docker run invocation is
built entirely from trusted, on-disk exercise definitions plus a
validated session directory — never from a client-supplied command.

Wire protocol, one JSON line per request over a plain TCP connection
(newline-terminated, see _read_request):

  {"op": "start", "session_id", "exercise_id", "session_dir", "cols", "rows"}
    -> {"ok": true} or {"ok": false, "error": "..."}, then (on ok) the
    connection becomes a raw duplex byte relay to the sandboxed nvim's
    pty for the rest of the session. The connection closing (either
    direction) is itself the "stop" signal — it tears the container down
    — so there's no separate stop op.

  {"op": "resize", "session_id", "cols", "rows"} -> {"ok": bool}, then
    closes. A short-lived side channel, since the data connection is
    raw bytes with nowhere to carry an out-of-band signal.

At startup, also builds the sandbox images (scripts/build_exercise_images.py)
— folded in here rather than kept as a separate sandbox-builder service,
so exactly one container in this stack ever needs docker.sock.
"""

import asyncio
import fcntl
import json
import logging
import os
import pty
import re
import signal
import struct
import subprocess
import sys
import termios

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import exercises as exercises_mod  # noqa: E402
from scripts import build_exercise_images  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("vim-caddie-launcher")

HOST = os.environ.get("VIM_CADDIE_LAUNCHER_HOST", "0.0.0.0")
PORT = int(os.environ.get("VIM_CADDIE_LAUNCHER_PORT", "9000"))
SESSIONS_ROOT = os.path.realpath(
    os.environ.get("VIM_CADDIE_SESSIONS_DIR", os.path.join(os.path.expanduser("~"), ".cache", "vim-caddie", "sessions"))
)
SESSION_FILE_MAX_BYTES = 2_000_000

_SESSION_ID_RE = re.compile(r"^[a-f0-9]{1,32}$")

# session_id -> (proc, master_fd) — populated by _handle_start, read by
# _handle_resize on a separate connection. No lock: both only ever touch
# a given entry from the event loop thread, never concurrently with each
# other for the same session_id (resize can't race a start it depends on).
_SESSIONS = {}


def set_winsize(fd, rows, cols):
    packed = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, packed)


def _validate_session_dir(session_dir):
    real = os.path.realpath(session_dir)
    if os.path.commonpath([real, SESSIONS_ROOT]) != SESSIONS_ROOT or not os.path.isdir(real):
        raise ValueError(f"session_dir {session_dir!r} is not a valid session directory")
    return real


def _clamp(value, lo, hi, default):
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


def _docker_run_cmd(exercise, session_dir, container_name, cols, rows):
    """Identical hardened invocation this project has always used to spawn
    a sandbox — the only thing that changed is which process builds and
    runs it. See docker/nvim-sandbox/ for the image itself."""
    return [
        "docker", "run", "--rm", "-i", "-t",
        "--name", container_name,
        # No --user override: runs as the image's own baked-in `player`,
        # which owns nothing else on this host. Cross-uid access to the
        # socket it creates comes from an ACL backend already set on
        # session_dir (see nvim_session.py), not a shared uid.
        "--env", "HOME=/tmp",
        "--network", "none",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=32m,mode=1777",
        "--cap-drop", "ALL",
        # --security-opt no-new-privileges omitted: breaks `exec` under
        # snap-packaged Docker (AppArmor/no_new_privs interaction). The
        # other flags here already cover the same ground for a
        # non-setuid binary like nvim; re-add it on a non-snap Docker.
        "--pids-limit", "64",
        "--memory", "256m",
        "--memory-swap", "256m",
        "--cpus", "0.5",
        "--ulimit", "nofile=128:128",
        "--ulimit", f"fsize={SESSION_FILE_MAX_BYTES}:{SESSION_FILE_MAX_BYTES}",
        # --ulimit nproc deliberately NOT set: RLIMIT_NPROC is enforced
        # per real UID across the whole host, not scoped to this
        # container — a low value here fails against unrelated processes
        # elsewhere on the host under the same uid. --pids-limit above is
        # the correctly cgroup-scoped equivalent.
        "--ipc", "none",
        "-v", f"{session_dir}:/state",
        exercise["image"],
        "--listen", "/state/nvim.sock",
        "-u", "/state/init.vim",
        "+call cursor({}, {})".format(exercise["cursor_start"]["line"], exercise["cursor_start"]["col"]),
        f"/state/workspace/{exercise['open_file']}",
    ]


async def _read_request(reader):
    line = await reader.readline()
    if not line:
        return None
    return json.loads(line)


async def _reply(writer, **payload):
    writer.write((json.dumps(payload) + "\n").encode())
    await writer.drain()


async def _handle_start(reader, writer, req):
    session_id = str(req.get("session_id", ""))
    if not _SESSION_ID_RE.match(session_id):
        await _reply(writer, ok=False, error="invalid session_id")
        return
    try:
        exercise = exercises_mod.load_exercise(req.get("exercise_id", ""))
        session_dir = _validate_session_dir(req.get("session_dir", ""))
    except (FileNotFoundError, ValueError) as e:
        await _reply(writer, ok=False, error=str(e))
        return
    cols = _clamp(req.get("cols"), 1, 500, 80)
    rows = _clamp(req.get("rows"), 1, 500, 24)
    container_name = f"vim-caddie-{session_id}"

    master_fd, slave_fd = pty.openpty()
    set_winsize(slave_fd, rows, cols)
    docker_cmd = _docker_run_cmd(exercise, session_dir, container_name, cols, rows)
    proc = subprocess.Popen(docker_cmd, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, start_new_session=True)
    os.close(slave_fd)
    _SESSIONS[session_id] = (proc, master_fd)
    log.info("session %s: started container=%s exercise=%s", session_id, container_name, exercise["id"])
    await _reply(writer, ok=True)

    loop = asyncio.get_running_loop()

    def on_master_readable():
        try:
            data = os.read(master_fd, 65536)
        except OSError:
            data = b""
        if not data:
            try:
                loop.remove_reader(master_fd)
            except Exception:
                pass
            writer.close()
            return
        writer.write(data)

    loop.add_reader(master_fd, on_master_readable)
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            try:
                os.write(master_fd, data)
            except OSError:
                break
    except (OSError, ConnectionResetError):
        pass
    finally:
        try:
            loop.remove_reader(master_fd)
        except Exception:
            pass
        _SESSIONS.pop(session_id, None)
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        # Belt and suspenders: --rm should already remove it once
        # stopped, but do it explicitly in case signal relay didn't.
        subprocess.run(
            ["docker", "stop", "-t", "2", container_name],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        try:
            os.close(master_fd)
        except OSError:
            pass
        log.info("session %s: torn down", session_id)


async def _handle_resize(writer, req):
    session_id = str(req.get("session_id", ""))
    entry = _SESSIONS.get(session_id)
    if entry is None:
        await _reply(writer, ok=False, error="unknown session")
        return
    proc, master_fd = entry
    cols = _clamp(req.get("cols"), 1, 500, 80)
    rows = _clamp(req.get("rows"), 1, 500, 24)
    try:
        set_winsize(master_fd, rows, cols)
        if proc.pid:
            os.killpg(proc.pid, signal.SIGWINCH)
    except OSError:
        pass
    await _reply(writer, ok=True)


async def _handle_conn(reader, writer):
    try:
        req = await _read_request(reader)
        if req is None:
            return
        op = req.get("op")
        if op == "start":
            await _handle_start(reader, writer, req)
        elif op == "resize":
            await _handle_resize(writer, req)
        else:
            await _reply(writer, ok=False, error="unknown op")
    except Exception:
        log.exception("connection handler failed")
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def main():
    log.info("building sandbox images...")
    build_exercise_images.main()
    server = await asyncio.start_server(_handle_conn, HOST, PORT)
    log.info("launcher listening on %s:%s", HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
