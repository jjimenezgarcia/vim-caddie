#!/usr/bin/env python3
"""Verifies an exercise the same way every exercise in exercises/*.json was
actually built: drive a real, headless Neovim through `ideal_keystrokes`
and check the resulting buffer/cursor against `success` — never hand-trust
that a keystroke sequence does what it looks like it does. See
docs/how-to-write-an-exercise.md for the authoring workflow this supports.

Two ways to use it:

  1. Check an exercise already sitting in exercises/*.json:
       python scripts/verify_exercise.py <exercise-id>
     (only meaningful for one that still has ideal_keystrokes — a scrubbed
     professional/genius exercise has nothing left here to replay; see
     scripts/gen_all_results.py.)

  2. Import verify_and_write() while iterating on a not-yet-saved
     exercise, and only touch exercises/<id>.json once it actually passes
     — see docs/how-to-write-an-exercise.md for a full example.
"""

import json
import os
import shutil
import sys
import tempfile

import pynvim

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXERCISES_DIR = os.path.join(REPO_ROOT, "exercises")
sys.path.insert(0, os.path.join(REPO_ROOT, "server"))

from exercises import (  # noqa: E402
    CONCEPT_TIER,
    TIER_PAR_FLOOR,
    DIFFICULTY_TIERS,
    difficulty_for_exercise,
    load_exercise,
)


def load_text_as_buffer(text):
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n")


def run(workspace, open_file, cursor_start, keystrokes, set_cmds=None, final_file=None):
    """Seeds a scratch dir with `workspace`, opens `open_file` in a real
    headless Neovim (-u NONE: no config, deterministic), feeds it
    `keystrokes` via nvim_input, and returns the resulting buffer lines +
    cursor of `final_file` (defaults to `open_file` — pass this only when
    success checks a *different* file than the one that was edited)."""
    tmpdir = tempfile.mkdtemp(prefix="vimcaddie-verify-")
    try:
        for name, text in workspace.items():
            with open(os.path.join(tmpdir, name), "w", encoding="utf-8") as f:
                f.write(text)
        prev_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            nvim = pynvim.attach("child", argv=["nvim", "--embed", "--headless", "-u", "NONE", "-n", open_file])
        finally:
            os.chdir(prev_cwd)
        try:
            for cmd in set_cmds or []:
                nvim.command(cmd)
            nvim.current.window.cursor = (cursor_start["line"], cursor_start["col"] - 1)
            nvim.input(keystrokes)
            nvim.command("redraw")
            target = final_file or open_file
            nvim.command(f"buffer {target}")
            lines = nvim.request("nvim_buf_get_lines", 0, 0, -1, False)
            cursor = nvim.request("nvim_win_get_cursor", 0)
            return lines, cursor
        finally:
            nvim.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def tier_for_theory(related_theory):
    """None means "genius or the one apprentice free-play exercise" —
    both have empty related_theory by design (see
    server/exercises.py's difficulty_for_exercise) — caller must know
    which one it's dealing with from context."""
    tiers = [CONCEPT_TIER.get(t, DIFFICULTY_TIERS[0]) for t in (related_theory or [])]
    if not tiers:
        return None
    return max(tiers, key=DIFFICULTY_TIERS.index)


def check_exercise(spec):
    """spec is a full exercise dict plus one extra key, "tier" — the
    INTENDED tier, checked against what CONCEPT_TIER actually derives
    from spec['related_theory'] (must agree, or this exercise would be
    silently mis-tiered the moment it's loaded for real) and against
    TIER_PAR_FLOOR (par must clear the tier's floor; there's no
    ceiling — see server/exercises.py's module comment on why). Returns
    (ok: bool, message: str)."""
    s = spec["success"]
    final_file = s.get("file", spec["open_file"])
    lines, cursor = run(
        spec["workspace"], spec["open_file"], spec["cursor_start"], spec["ideal_keystrokes"],
        spec.get("set_cmds"), final_file=final_file,
    )
    if s["type"] == "buffer_match":
        expected = load_text_as_buffer(s["content"])
        ok = lines == expected
        detail = "" if ok else f"got={lines}\n  expected={expected}"
    elif s["type"] == "cursor_at":
        got_line, got_col0 = cursor
        got_col = got_col0 + 1
        ok = got_line == s["line"] and got_col == s["col"]
        detail = "" if ok else f"cursor=({got_line},{got_col}) expected=({s['line']},{s['col']})"
    else:
        return False, f"unknown success type {s['type']!r}"

    par = len(spec["ideal_keystrokes"])
    derived = tier_for_theory(spec.get("related_theory"))
    tier_ok = derived == spec["tier"] if derived is not None else spec["tier"] == "genius"
    floor = TIER_PAR_FLOOR[spec["tier"]]
    par_ok = par >= floor

    ok_all = ok and tier_ok and par_ok
    msg = f"tier={spec['tier']} (derived={derived}) par={par} (floor {floor})"
    if not ok:
        msg += f"\n  {detail}"
    if not tier_ok:
        msg += f"\n  related_theory implies '{derived}', not '{spec['tier']}' — fix one or the other"
    if not par_ok:
        msg += f"\n  par {par} is below the '{spec['tier']}' floor of {floor}"
    return ok_all, msg


def verify_and_write(spec, write=True):
    """Use while iterating on a not-yet-saved exercise: pass a full spec
    dict (see docs/how-to-write-an-exercise.md), get real headless-Neovim
    verification, and only write exercises/<id>.json once it actually
    passes."""
    ok, msg = check_exercise(spec)
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {spec['id']:28} {msg}")

    if ok and write:
        out = {
            "id": spec["id"], "title": spec["title"], "description": spec["description"],
            "par": len(spec["ideal_keystrokes"]), "ideal_keystrokes": spec["ideal_keystrokes"],
            "workspace": spec["workspace"], "open_file": spec["open_file"], "success": spec["success"],
            "permissions": spec.get("permissions", {"commands": []}), "cursor_start": spec["cursor_start"],
            "related_theory": spec.get("related_theory", []), "objective": spec["objective"],
        }
        if spec.get("prerequisites"):
            out["prerequisites"] = spec["prerequisites"]
        path = os.path.join(EXERCISES_DIR, f"{spec['id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return ok


def main():
    if len(sys.argv) != 2:
        print("usage: python scripts/verify_exercise.py <exercise-id>", file=sys.stderr)
        sys.exit(2)
    exercise_id = sys.argv[1]
    try:
        ex = load_exercise(exercise_id)  # full, unredacted -- this script has trusted local fs access
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    if not ex.get("ideal_keystrokes"):
        print(f"'{exercise_id}' has no ideal_keystrokes on disk (likely a scrubbed "
              f"professional/genius exercise, or a reach_markers free-play one) — nothing to replay.")
        sys.exit(0)
    spec = dict(ex)
    spec["tier"] = difficulty_for_exercise(ex)
    ok, msg = check_exercise(spec)
    print(f"[{'OK' if ok else 'FAIL'}] {exercise_id:28} {msg}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
