# The one component in this stack with docker.sock mounted — see
# docker-compose.yml and server/launcher.py's module docstring for why
# it's split out from backend this way. Kept deliberately minimal: pure
# stdlib Python (no requirements.txt, no third-party packages at all) plus
# the `docker` CLI binary, nothing else — the smaller this image's own
# dependency surface, the smaller the blast radius of a bug in the one
# process that can reach the host daemon.
FROM python:3.12-slim

# docker-cli (not docker.io, which on this base pulls in the daemon too —
# confirmed by testing, not assumed): only ever talks to the *host's*
# daemon over the socket bind-mounted in at runtime, never runs its own.
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker-cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server/exercises.py server/exercises.py
COPY server/launcher.py server/launcher.py
COPY scripts/ scripts/
COPY exercises/ exercises/
COPY docker/nvim-sandbox/ docker/nvim-sandbox/

WORKDIR /app/server
CMD ["python", "launcher.py"]
