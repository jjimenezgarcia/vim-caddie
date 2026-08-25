# Build context is the repo root (see docker-compose.yml) — the frontend
# needs package.json/index.html/vite+tailwind configs/src/, all at root.
FROM node:20-slim AS build

WORKDIR /app

# Dependency layer cached independently of source changes
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# VITE_VIM_CADDIE_WS_URL / VITE_VIM_CADDIE_HTTP_URL are baked in at build
# time (Vite convention — there's no such thing as a runtime env var for
# a static SPA), which is exactly why they're optional here: unset, the
# already-existing code fallback (src/useNvimSession.js,
# src/auth.js — "ws://localhost:8765" / "http://localhost:8765") kicks
# in, which is already correct for "docker compose up on your own
# machine, open it in your own browser" — the common case this compose
# setup targets. Only deploying this somewhere the browser *isn't* on
# the same host needs these actually set (see README's Deployment section).
ARG VITE_VIM_CADDIE_WS_URL
ARG VITE_VIM_CADDIE_HTTP_URL
# ARG alone doesn't reach the RUN step's process environment (Docker only
# substitutes it into other Dockerfile instructions) — Vite reads
# import.meta.env.VITE_* from real env vars at build time, so it has to
# be promoted to ENV to actually take effect.
ENV VITE_VIM_CADDIE_WS_URL=${VITE_VIM_CADDIE_WS_URL}
ENV VITE_VIM_CADDIE_HTTP_URL=${VITE_VIM_CADDIE_HTTP_URL}
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
