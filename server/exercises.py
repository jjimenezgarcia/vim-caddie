"""Loads exercise manifests from ../exercises/*.json and resolves each
one's permission whitelist to the Docker image tag that actually has (and
only has) those tools installed — see scripts/build_exercise_images.py for
what builds those images, and docker/nvim-sandbox/command_packages.json
for the allowlist of what's even eligible to be whitelisted.
"""

import hashlib
import json
import os
import re

EXERCISES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exercises")
BASE_IMAGE = os.environ.get("VIM_CADDIE_BASE_IMAGE", "vim-caddie-nvim")

_VALID_ID = re.compile(r"^[a-zA-Z0-9_-]+$")

DIFFICULTY_TIERS = ["apprentice", "beginner", "intermediate", "advanced", "professional", "genius"]

CONCEPT_TIER = {
    "vim-big-word-motions": "apprentice",
    "vim-delete-character": "apprentice",
    "vim-file-start-end": "apprentice",
    "vim-find-char-motions": "apprentice",
    "vim-hjkl-motions": "apprentice",
    "vim-insert-entry-points": "apprentice",
    "vim-insert-mode-editing": "apprentice",
    "vim-insert-resume": "apprentice",
    "vim-line-operators": "apprentice",
    "vim-line-start-end": "apprentice",
    "vim-operators": "apprentice",
    "vim-operators-and-motions": "apprentice",
    "vim-paste": "apprentice",
    "vim-paste-and-move": "apprentice",
    "vim-replace-character": "apprentice",
    "vim-substitute-shorthand": "apprentice",
    "vim-toggle-case-character": "apprentice",
    "vim-undo": "apprentice",
    "vim-word-end-backward": "apprentice",
    "vim-word-motions": "apprentice",
    "vim-automatic-marks": "beginner",
    "vim-counts": "beginner",
    "vim-end-of-line-operators": "beginner",
    "vim-indent": "beginner",
    "vim-join-lines": "beginner",
    "vim-join-without-space": "beginner",
    "vim-marks": "beginner",
    "vim-reindent": "beginner",
    "vim-search": "beginner",
    "vim-shell-commands": "beginner",
    "vim-substitute": "beginner",
    "vim-visual-mode": "beginner",
    "vim-visual-replace": "beginner",
    "vim-visual-swap-ends": "beginner",
    "vim-word-text-objects": "beginner",
    "vim-black-hole-register": "intermediate",
    "vim-buffers": "intermediate",
    "vim-dot-repeat": "intermediate",
    "vim-increment-decrement": "intermediate",
    "vim-insert-register-paste": "intermediate",
    "vim-jumplist": "intermediate",
    "vim-percent-match": "intermediate",
    "vim-registers": "intermediate",
    "vim-replace-mode": "intermediate",
    "vim-search-word": "intermediate",
    "vim-substitute-range": "intermediate",
    "vim-text-objects-extended": "intermediate",
    "vim-visual-line-and-block": "intermediate",
    "vim-windows": "intermediate",
    "vim-case-operators": "advanced",
    "vim-copy-move-lines": "advanced",
    "vim-ex-ranges": "advanced",
    "vim-global-command": "advanced",
    "vim-gn-motion": "advanced",
    "vim-macro-append": "advanced",
    "vim-macros": "advanced",
    "vim-paragraph-sentence-motions": "advanced",
    "vim-regex-basics": "advanced",
    "vim-register-types": "advanced",
    "vim-reselect-visual": "advanced",
    "vim-substitute-confirm": "advanced",
    "vim-tag-text-objects": "advanced",
    "vim-visual-block-insert": "advanced",
    "vim-expression-register": "professional",
    "vim-format-paragraph": "professional",
    "vim-global-marks": "professional",
    "vim-inverse-global": "professional",
    "vim-normal-over-range": "professional",
    "vim-recursive-macro": "professional",
    "vim-sequential-increment": "professional",
    "vim-sort-command": "professional",
}

# Not a difficulty signal on its own — repetition can't teach two concepts
# a keystroke total can't either — but a genuinely concept-rich solution
# still shouldn't be trivially short for its tier. This is a floor to
# catch an exercise mis-tagged well above what it actually does, checked
# only at authoring time (see the verification harness), never at runtime.
TIER_PAR_FLOOR = {
    "apprentice": 0,
    "beginner": 10,
    "intermediate": 25,
    "advanced": 40,
    "professional": 55,
    "genius": 90,
}


def difficulty_for_exercise(ex):
    theory = ex.get("related_theory") or []
    if not theory:
        return "genius" if ex.get("par") is not None else DIFFICULTY_TIERS[0]
    tiers = [CONCEPT_TIER.get(topic, DIFFICULTY_TIERS[0]) for topic in theory]
    return max(tiers, key=DIFFICULTY_TIERS.index)


def image_tag(commands):
    """The tag scripts/build_exercise_images.py builds for this exact
    whitelist. Empty list -> the base image itself (no derived variant)."""
    if not commands:
        return BASE_IMAGE
    key = ",".join(sorted(set(commands)))
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"{BASE_IMAGE}:perm-{digest}"


def load_exercise(exercise_id):
    if not _VALID_ID.match(exercise_id or ""):
        raise FileNotFoundError(f"no exercise named {exercise_id!r}")
    path = os.path.join(EXERCISES_DIR, f"{exercise_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"no exercise named {exercise_id!r}")
    with open(path, "r", encoding="utf-8") as f:
        ex = json.load(f)
    ex.setdefault("permissions", {}).setdefault("commands", [])
    ex.setdefault("cursor_start", {}).setdefault("line", 1)
    ex["cursor_start"].setdefault("col", 1)
    ex.setdefault("related_theory", [])
    ex.setdefault("prerequisites", [])
    ex.setdefault("objective", [])
    ex["image"] = image_tag(ex["permissions"]["commands"])
    return ex


def list_exercises():
    if not os.path.isdir(EXERCISES_DIR):
        return []
    loaded = []
    for name in sorted(os.listdir(EXERCISES_DIR)):
        if not name.endswith(".json"):
            continue
        try:
            loaded.append(load_exercise(name[: -len(".json")]))
        except (json.JSONDecodeError, OSError):
            continue
    titles_by_id = {ex["id"]: ex["title"] for ex in loaded}

    out = []
    for ex in loaded:
        prerequisites = [
            {"id": pid, "title": titles_by_id[pid]} for pid in ex["prerequisites"] if pid in titles_by_id
        ]
        difficulty = difficulty_for_exercise(ex)
        reveals_solution = DIFFICULTY_TIERS.index(difficulty) > DIFFICULTY_TIERS.index("advanced")
        out.append(
            {
                "id": ex["id"],
                "title": ex["title"],
                "description": ex["description"],
                "par": ex.get("par"),
                "difficulty": difficulty,
                "prerequisites": prerequisites,
                "related_theory": ex["related_theory"],
                "objective": ex["objective"],
                "ideal_keystrokes": "" if reveals_solution else ex.get("ideal_keystrokes", ""),
                "workspace": {} if reveals_solution else ex.get("workspace", {}),
                "open_file": ex.get("open_file"),
                "cursor_start": ex["cursor_start"],
                "success": {} if reveals_solution else ex.get("success", {}),
            }
        )
    return out
