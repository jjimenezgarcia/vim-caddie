# Base image shared by every permission tier. `init.vim` and the exercise's
# workspace files are NOT baked in here — they're generated per-session by
# the backend (server/vimrc.py) and written into the session's bind-mounted
# /state dir, so changing an exercise's editor config or seed files never
# needs an image rebuild. Only the *tool whitelist* (this Dockerfile's
# apt-get install line) does — see scripts/build_exercise_images.py, which
# builds one derived image per distinct set of exercises.*.permissions.commands.
FROM debian:bookworm-slim

ARG EXTRA_PACKAGES=""

RUN apt-get update \
    && apt-get install -y --no-install-recommends neovim ${EXTRA_PACKAGES} \
    && rm -rf /var/lib/apt/lists/*

# None of these do anything for this product — they're just standard
# Debian base-image baggage (login/passwd/mount packages) with the setuid
# bit set. Hardening.
RUN rm -f /usr/bin/mount /usr/bin/umount /usr/bin/su /usr/bin/passwd \
    /usr/bin/chsh /usr/bin/chfn /usr/bin/newgrp /usr/bin/gpasswd \
    /usr/bin/chage /usr/bin/expiry /usr/sbin/unix_chkpwd

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin player

USER player
WORKDIR /state/workspace

ENTRYPOINT ["nvim"]
