#!/usr/bin/env python3
"""Regenerates all_results.md from exercises/*.json, then scrubs
`ideal_keystrokes` out of every professional/genius exercises/*.json file
it just archived — those two tiers' solutions are meant to exist *only*
in all_results.md, never in the file the live app actually loads (see
server/nvim_session.py: NvimSession works fine with par set and
ideal_keystrokes absent — it just skips live per-keystroke hit/miss
feedback, which would otherwise leak the hidden solution one correct
keystroke at a time). Run this after authoring or redesigning any
exercise, public or private.

Why a separate vault (private_solutions.json), not just exercises/*.json:
after the first run scrubs a professional/genius exercise, its JSON file
no longer has ideal_keystrokes to archive — a naive "regenerate from
exercises/*.json" on a *second* run would find nothing there and
overwrite that exercise's already-correct all_results.md entry with "no
fixed reference path", permanently losing it. The vault is where a
professional/genius solution is captured (the moment it's still present
in the live JSON, right before scrubbing) and stays put afterward,
untouched by anything scrubbing the live files. Both private_solutions.json
and all_results.md are gitignored.

Usage: python scripts/gen_all_results.py
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXERCISES_DIR = os.path.join(REPO_ROOT, "exercises")
VAULT_PATH = os.path.join(REPO_ROOT, "private_solutions.json")
sys.path.insert(0, os.path.join(REPO_ROOT, "server"))

from exercises import list_exercises, load_exercise, DIFFICULTY_TIERS  # noqa: E402

TIER_TITLES = {
    "apprentice": "Apprentice",
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
    "professional": "Professional",
    "genius": "Genius",
}
PUBLIC_TIERS = {"apprentice", "beginner", "intermediate", "advanced"}
PRIVATE_TIERS = {"professional", "genius"}


def load_vault():
    if not os.path.exists(VAULT_PATH):
        return {}
    with open(VAULT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_vault(vault):
    with open(VAULT_PATH, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def main():
    listed = {e["id"]: e for e in list_exercises()}
    vault = load_vault()

    by_tier = {t: [] for t in DIFFICULTY_TIERS}
    to_scrub = []  # (id, path) for professional/genius files that still have ideal_keystrokes
    for eid in sorted(listed):
        path = os.path.join(EXERCISES_DIR, f"{eid}.json")
        ex = load_exercise(eid)  # full, unredacted -- this script has trusted local fs access
        tier = listed[eid]["difficulty"]
        by_tier[tier].append(ex)

        keystrokes = ex.get("ideal_keystrokes")
        if tier in PRIVATE_TIERS and keystrokes:
            vault[eid] = keystrokes  # capture into the vault before it's gone from the live file
            to_scrub.append((eid, path))

    save_vault(vault)

    lines = [
        "# All exercise solutions",
        "",
        "Every exercise's reference solution. Public tiers are generated "
        "fresh from `exercises/*.json` every run; professional/genius come "
        "from `private_solutions.json` (see this script's docstring for "
        "why). Regenerate with `scripts/gen_all_results.py` after any "
        "exercise content change.",
        "",
        "**Public tiers** (apprentice/beginner/intermediate/advanced) already "
        "show their solution to players in-app (\"Show solution\") — nothing "
        "here is secret for those. **Professional and genius are private**: "
        "the app deliberately never reveals their solution — not in the "
        "browse list (`server/exercises.py`'s `list_exercises()` redaction), "
        "not in the UI (`src/lib/difficulty.js`'s `solutionAllowed`), and not "
        "even to the live game session itself (`ideal_keystrokes` isn't "
        "stored in these two tiers' `exercises/*.json` at all — this file "
        "and `private_solutions.json` are the only place the answers exist "
        "in full). Both are in `.gitignore` and never committed.",
        "",
    ]

    for tier in DIFFICULTY_TIERS:
        exs = by_tier[tier]
        if not exs:
            continue
        visibility = "public — shown in-app" if tier in PUBLIC_TIERS else "PRIVATE — never shown in-app"
        lines.append(f"## {TIER_TITLES[tier]} ({visibility})")
        lines.append("")
        for ex in exs:
            lines.append(f"### {ex['title']} (`{ex['id']}`)")
            lines.append("")
            lines.append(f"- par: {ex.get('par')}")
            lines.append(f"- open file: `{ex.get('open_file')}`")
            keystrokes = ex.get("ideal_keystrokes") or vault.get(ex["id"])
            if keystrokes:
                lines.append("- ideal_keystrokes:")
                lines.append("")
                lines.append("```")
                lines.append(repr(keystrokes))
                lines.append("```")
            else:
                success = ex.get("success", {})
                if success.get("type") == "reach_markers":
                    lines.append(f"- no fixed reference path (free play — reach {success.get('count')} markers)")
                else:
                    lines.append("- no fixed reference path")
            lines.append("")

    out_path = os.path.join(REPO_ROOT, "all_results.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"wrote {out_path}: {sum(len(v) for v in by_tier.values())} exercises")

    for eid, path in to_scrub:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.pop("ideal_keystrokes", None)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    if to_scrub:
        print(f"scrubbed ideal_keystrokes from {len(to_scrub)} private exercise file(s): "
              f"{', '.join(eid for eid, _ in to_scrub)}")


if __name__ == "__main__":
    main()
