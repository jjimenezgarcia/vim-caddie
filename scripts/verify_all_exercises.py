#!/usr/bin/env python3
"""CI check: every public exercise's ideal_keystrokes actually produces its
claimed success state, verified against a real headless Neovim.

Skipped, not failed:
  - professional/genius exercises — scripts/gen_all_results.py deliberately
    scrubs their ideal_keystrokes out of exercises/*.json (see its
    PRIVATE_TIERS), archiving the real solution in the gitignored
    private/ vault instead. There's nothing left here to replay for them,
    by design.
  - reach_markers free-play exercises — no fixed solution path exists for
    those either.

Failed, not skipped:
  - a professional/genius exercise whose ideal_keystrokes is still present
    in exercises/*.json — a forgotten `python scripts/gen_all_results.py`
    before committing, which would otherwise leak a private solution into
    version control.

Usage: python scripts/verify_all_exercises.py
"""

import glob
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXERCISES_DIR = os.path.join(REPO_ROOT, "exercises")
sys.path.insert(0, os.path.join(REPO_ROOT, "server"))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from exercises import difficulty_for_exercise, load_exercise  # noqa: E402
from gen_all_results import PRIVATE_TIERS  # noqa: E402
from verify_exercise import check_exercise  # noqa: E402


def main():
    ids = sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(EXERCISES_DIR, "*.json"))
    )
    failures = []
    checked = 0
    skipped = 0

    for exercise_id in ids:
        try:
            ex = load_exercise(exercise_id)
            tier = difficulty_for_exercise(ex)
            has_keystrokes = bool(ex.get("ideal_keystrokes"))

            if tier in PRIVATE_TIERS:
                if has_keystrokes:
                    failures.append(
                        f"{exercise_id}: {tier} exercise still has ideal_keystrokes in "
                        f"exercises/{exercise_id}.json — run scripts/gen_all_results.py "
                        f"before committing"
                    )
                    print(f"[FAIL] {exercise_id:32} private tier but not scrubbed")
                else:
                    skipped += 1
                continue

            if not has_keystrokes:
                skipped += 1  # reach_markers free play, or similar
                continue

            spec = dict(ex)
            spec["tier"] = tier
            ok, msg = check_exercise(spec)
            checked += 1
            print(f"[{'OK' if ok else 'FAIL'}] {exercise_id:32} {msg}")
            if not ok:
                failures.append(f"{exercise_id}: {msg}")
        except Exception as e:  # a malformed exercise is a real failure
            print(f"[FAIL] {exercise_id:32} raised {e!r}")
            failures.append(f"{exercise_id}: raised {e!r}")

    print(f"\n{checked} exercise(s) verified, {skipped} skipped (private or free-play).")

    if failures:
        print(f"\n{len(failures)} FAILURE(S):", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        sys.exit(1)

    print("all good.")


if __name__ == "__main__":
    main()
