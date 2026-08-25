# Runs server/app.py. Deliberately has no docker.sock and no `docker` CLI
# at all — see server/launcher.py's module docstring for why sandbox
# containers are spawned by a separate, minimal service instead. Build
# context is the repo root (see docker-compose.yml), since this needs
# server/ and exercises/ together, not just server/.
FROM python:3.12-slim

# acl: setfacl, used by server/nvim_session.py's NvimSession to grant the
# sandbox's own uid access to its session directory.
RUN apt-get update \
    && apt-get install -y --no-install-recommends acl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY server/ server/
COPY exercises/ exercises/

WORKDIR /app/server
CMD ["python", "app.py"]
