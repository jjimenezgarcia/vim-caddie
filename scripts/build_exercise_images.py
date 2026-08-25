#!/usr/bin/env python3
"""Builds the base sandbox image plus one derived image per distinct
permission whitelist used by any exercise in exercises/*.json.

Run this whenever exercises/ changes what commands it whitelists, or
docker/nvim-sandbox/Dockerfile itself changes. Safe to re-run any time —
`docker build` no-ops on unchanged layers, and each derived image is
tagged by a hash of its exact command set (see server/exercises.py's
image_tag()), so unrelated exercises sharing a whitelist share an image.

Usage: python scripts/build_exercise_images.py
"""

import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from server.exercises import BASE_IMAGE, EXERCISES_DIR, image_tag  # noqa: E402

DOCKERFILE_DIR = os.path.join(REPO_ROOT, "docker", "nvim-sandbox")
PACKAGES_MANIFEST = os.path.join(DOCKERFILE_DIR, "command_packages.json")


def load_command_packages():
    with open(PACKAGES_MANIFEST, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_comment", None)
    return data


def collect_permission_sets():
    sets = set()
    for name in sorted(os.listdir(EXERCISES_DIR)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(EXERCISES_DIR, name), "r", encoding="utf-8") as f:
            ex = json.load(f)
        commands = tuple(sorted(set(ex.get("permissions", {}).get("commands", []))))
        if commands:
            sets.add(commands)
    return sets


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def main():
    print(f"== building base image: {BASE_IMAGE} ==")
    run(["docker", "build", "-t", BASE_IMAGE, DOCKERFILE_DIR])

    command_packages = load_command_packages()
    permission_sets = collect_permission_sets()

    if not permission_sets:
        print("no exercises whitelist any commands — nothing else to build")
        return

    for commands in sorted(permission_sets):
        unknown = [c for c in commands if c not in command_packages]
        if unknown:
            print(
                f"!! skipping permission set {commands}: {unknown} not in "
                f"{PACKAGES_MANIFEST} — add them there first",
                file=sys.stderr,
            )
            continue
        packages = sorted({command_packages[c] for c in commands})
        tag = image_tag(list(commands))
        print(f"== building {tag} (commands={list(commands)}, packages={packages}) ==")
        run(
            [
                "docker", "build",
                "--build-arg", f"EXTRA_PACKAGES={' '.join(packages)}",
                "-t", tag,
                DOCKERFILE_DIR,
            ]
        )

    print("done.")


if __name__ == "__main__":
    main()
