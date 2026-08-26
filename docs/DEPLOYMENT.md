# Deployment

> Back to [README](../README.md).

Requirements: Docker with Compose v2 (`docker compose`, not the old
standalone `docker-compose`), and a Docker daemon this host can spawn
sibling containers on (see "How this works" below for why that matters).

```sh
git clone <this repo> && cd vim-caddie
docker compose up --build
```

Then open **http://localhost:8080**. First run takes a few minutes — it
also builds the sandboxed Neovim image(s) each exercise actually runs in
(`launcher`'s startup step, before it starts accepting sessions). Every
later `docker compose up` reuses what's already built.

That's the whole setup for running this on your own machine. Nothing
below is required unless something doesn't fit your environment.

## How this works

Three services, defined in `docker-compose.yml`, on two internal networks:

- **`frontend`** — the React app, built to static files and served by
  nginx (`docker/frontend/`). The only service published to the host, on
  `:8080`. nginx also reverse-proxies `/ws` (the WebSocket game
  connection) and the `/api/` HTTP endpoints to `backend` over the
  `internal` network — see `docker/frontend/nginx.conf`.
- **`backend`** — `server/app.py` (`docker/backend/`). Not published;
  only reachable from other containers on `internal`. Runs untrusted
  player keystrokes through a real Neovim process per session, so it's
  the thing in this stack actually facing that input.
- **`launcher`** — `server/launcher.py` (`docker/launcher/`). Spawns the
  actual sandboxed Neovim container per exercise session, on request from
  `backend` over a *second*, separate network (`docker-control`) that
  `frontend` isn't attached to at all. Also builds the sandbox images
  once at startup (`scripts/build_exercise_images.py`, folded in here
  rather than kept as its own service).

**The docker.sock split is the security-relevant part.** Spawning a
sandboxed container per exercise needs a Docker daemon reachable from
inside a container — the standard "Docker-outside-of-Docker" pattern (no
nested daemon; both talk to the *host's* real one over the socket). The
naive version of this bind-mounts `docker.sock` straight into `backend`
— but `backend` is also the thing parsing untrusted player input through
a real terminal session, and a socket mount gives whoever holds it the
same practical control over the host as root: create, inspect, or remove
*any* container on that host, not just the sandboxed ones this app
spawns. A full RCE in `backend` would be a straight line to host root.

So `docker.sock` is mounted into `launcher` only, and `launcher` exposes
`backend` nothing resembling the Docker API — just two operations, over a
network `frontend` can't even resolve `launcher`'s hostname on: "start a
sandbox for this known exercise" and "resize its pty." Both are built
entirely from trusted, on-disk exercise definitions and a
path-validated session directory, never from a client-supplied command —
see `server/launcher.py`'s module docstring for the full reasoning,
including why a generic "Docker socket proxy" (allowlisting which API
endpoints are reachable) doesn't actually close this gap on its own: it
doesn't inspect what's *inside* an allowed call's body, so a compromised
caller can still ask an allowed "create container" call for
`Privileged: true` and a host bind mount. Here, `backend` never
constructs a Docker command at all, so there's nothing like that for a
compromised `backend` to ask for. The per-exercise sandbox itself is
hardened the same way it always was regardless of who spawns it
(`--network none`, `--read-only`, `--cap-drop ALL`, non-root, resource
limits — see `launcher.py`'s `_docker_run_cmd`).

If you want to go further: running the *host's* Docker daemon in
rootless mode means even full control of `docker.sock` isn't real root —
worth doing if your deployment environment supports it, though it's a
host-level setup decision this repo can't enforce from a compose file.

One consequence of DooD worth knowing if you customize anything: when
`launcher` tells the host daemon to bind-mount a session directory into a
sandbox container, that path is resolved by the *host*, not by
`launcher`'s own container — so the session-directory bind mount in
`docker-compose.yml` uses the identical absolute path across `launcher`
and `backend` (which writes the actual session files) on purpose. Don't
change one without the other.

## Configuration

Copy `.env.example` to `.env` to override anything — none of it is
required for a normal local setup:

- **`VIM_CADDIE_SESSIONS_DIR`** — where per-exercise session data lives
  on the host (default: `/var/lib/vim-caddie/sessions`). Override this if
  that path isn't writable/shareable on your setup (some Docker Desktop
  configurations, some snap-packaged Docker installs). Keep it short if
  you do: it becomes part of a real filesystem path a UNIX domain socket
  binds to, which the kernel caps at ~108 bytes total, full stop — a path
  buried inside a deeply-nested checkout plus a long username can
  actually blow past that (confirmed the hard way while building this).
- **`VITE_VIM_CADDIE_WS_URL`** / **`VITE_VIM_CADDIE_HTTP_URL`** — same-
  origin (the frontend's own host:port) is the default and is correct for
  any normal deployment, since nginx proxies to `backend` itself. Only
  set these if the frontend and backend genuinely need to be served from
  different origins. Baked into the frontend at *build* time (standard
  Vite behavior — there's no such thing as a runtime env var for a static
  single-page app), so changing them needs `docker compose build
  frontend` again, not just a restart.

## Where things persist

- **Accounts and progress**: a SQLite file in the `progress-data` named
  volume (`docker volume rm vim-caddie_progress-data` to wipe it).
- **Session data**: `VIM_CADDIE_SESSIONS_DIR` on the host, cleaned up
  automatically as each session ends — nothing to manage by hand.
