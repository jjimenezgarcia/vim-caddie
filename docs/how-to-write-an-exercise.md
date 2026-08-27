# How to write an exercise

An exercise is one file, `exercises/<id>.json`, plus (usually) one
[theory pill](how-to-write-pills.md) it points at. This document is
guidance for writing that file — the schema, the one rule that matters
more than the rest, and the tool you use to prove it actually works
before it ships.

## The one rule: difficulty is concepts combined, not keystrokes repeated

Read this section even if you skip the rest.

An exercise gets harder by requiring the player to combine *more
distinct concepts*, not by making them do the *same* thing more times.
"Delete 40 lines one at a time" and "delete 4 lines one at a time" test
identical understanding — the first is just longer, and longer-but-
identical is exhausting, not educational. It proves nothing a shorter
version didn't already prove.

A good exercise is built from several genuinely different sections, each
pairing this exercise's own concept with a *different* already-taught
concept — never the same pairing repeated. Two real examples already in
this repo:

- **`confirm-each-one`** (advanced, teaches confirm-substitute) — three
  sections: one needs a bulk substitute with *no* confirmation at all
  (teaching *when not to* reach for `gc`), one needs genuine per-match
  yes/no judgment calls, one adds quoted-value text objects into the mix.
  Nothing is repeated identically.
- **`number-every-list`** (professional, teaches sequential-increment) —
  five sections, each pairing the block-increment trick with a different
  earlier concept: a plain demo, fix-a-typo-first, remove-a-stray-line-
  first, remove-two-stray-lines-first, fix-case-first.

Why this matters more at the top tiers specifically: professional/genius
concepts (macros, `:sort`, the global command, sequential-increment) are
*efficiency* tools — their entire point is to compress many keystrokes
into few. A genuinely well-composed professional exercise is often
*shorter* than a well-composed advanced one, not longer. Padding with
repetition to hit a bigger number doesn't just fail to teach anything —
it actively fights against what the tier's own concept is for. See the
next section for how difficulty is actually measured, which was built
specifically to stop rewarding that padding.

## How difficulty is decided (you don't set it directly)

There's no `difficulty` field. Tier is *derived*, in
`server/exercises.py`:

1. Every theory pill has a `CONCEPT_TIER` entry — the tier it's first
   introduced at (hand-authored there, the same way `prerequisites` are
   hand-authored below — this genuinely can't be derived from anything
   else).
2. An exercise's tier is the **highest** tier among its own
   `related_theory` entries. Reusing an earlier concept alongside a new
   one doesn't lower the tier — that reuse is the whole point of the
   rule above.
3. **Genius is the deliberate exception**: those exercises introduce no
   concept of their own — they're capstones recombining several earlier
   ones — so `related_theory` is left `[]` on purpose, and `[]` *with* a
   `par` set is exactly what marks an exercise genius. (`[]` with no
   `par` at all is the one true edge case: a free-play exercise like
   `apple-hunt`, which has nothing to combine yet.)

`par` is **not** a difficulty signal to hit a target with — it's a
floor, checked only so an exercise isn't laughably short for what it
claims to teach (`TIER_PAR_FLOOR` in `server/exercises.py`: apprentice 0,
beginner 10, intermediate 25, advanced 40, professional 55, genius 90).
There is no ceiling. If your genuinely non-repetitive solution clears the
floor, it's done — don't pad it further.

## Schema

```jsonc
{
  "id": "confirm-each-one",            // matches the filename, kebab-case
  "title": "Confirm Each One",         // shown on the exercise card and page
  "description": "Learn how to review every match before replacing it, instead of all at once.",
  "par": 87,                            // = len(ideal_keystrokes) — set by the verifier, not you
  "ideal_keystrokes": "...",            // the reference solution, verified (see below)
  "workspace": { "review.txt": "..." }, // filename -> starting content
  "open_file": "review.txt",            // which workspace file nvim opens
  "cursor_start": { "line": 1, "col": 1 },
  "success": { "type": "buffer_match", "content": "..." },
  "permissions": { "commands": [] },
  "related_theory": ["vim-substitute-confirm"],
  "objective": ["...", "...", "..."],
  "prerequisites": ["proofread-the-file"]   // optional
}
```

- **`description`** is the generic, non-revealing blurb shown on the
  browse card and at the top of the exercise itself — "learn how to
  X," never "move the cursor onto the specific thing." **`objective`**
  is the detailed, step-by-step *what*, shown once the exercise is open
  — states the goal, deliberately never the keystrokes or commands to
  get there.
- **`workspace`** keys are plain filenames written into the session's
  sandbox — `open_file` must be one of them. `cursor_start` is
  1-indexed on both line and column (fed straight to Vimscript's
  `cursor(line, col)`), and matters: an `ideal_keystrokes` sequence that
  assumes the cursor already sits on the thing to fix needs this set
  correctly, or it'll edit the wrong spot.
- **`success`** is a discriminated union, three types:
  - `buffer_match` — `content` is the exact final buffer text. Add
    `"file"` if the exercise's target ends up in a *different* file than
    `open_file` (e.g. `fetch-and-return`-style exercises).
  - `cursor_at` — `line`/`col`, both 1-indexed, for pure-navigation
    exercises where the buffer never changes so `buffer_match` could
    never fire.
  - `reach_markers` — free play, no fixed keystroke path: the player
    chases `count` targets (`marker_char`) around a grid of
    `empty_char` cells, optionally `respawn`ing after each one. No `par`,
    no `ideal_keystrokes` at all for this type — see `apple-hunt.json`.
- **`permissions.commands`** whitelists shell commands the sandbox is
  allowed to run (`:!ls`, `:!cat file`, etc. — see the
  `vim-shell-commands` pill). Almost always `[]`. A command must already
  be listed in `docker/nvim-sandbox/command_packages.json` before any
  exercise can whitelist it — that file is itself an allowlist, kept to
  exactly what's actually used, not "anything that might be handy."
- **`prerequisites`** (optional) is a list of other exercise ids to
  recommend finishing first — a pedagogical judgment call, hand-authored
  like `CONCEPT_TIER`, not derivable. Keep it consistent with tier
  ordering: a prerequisite shouldn't land in a *harder* tier than the
  exercise recommending it (the verifier below doesn't check this across
  files — see "Before you're done").

## Verifying (never hand-trust a keystroke sequence)

Every exercise in this repo was built the same way: write a candidate,
run it against a real headless Neovim, and only keep it once the actual
resulting buffer matches. A keystroke sequence that "looks right" is not
verified — Vim has too many small surprises (sticky columns after a
vertical jump, `)` landing after the separating space, a literal `<` in
`ideal_keystrokes` getting parsed as key notation) for eyeballing to be
reliable.

`scripts/verify_exercise.py` is the tool:

```python
import sys
sys.path.insert(0, "scripts")
from verify_exercise import verify_and_write

spec = dict(
    id="confirm-each-one",
    tier="advanced",                       # the INTENDED tier — checked against
                                            # what related_theory actually derives to
    title="Confirm Each One",
    description="Learn how to review every match before replacing it, instead of all at once.",
    workspace={"review.txt": "temp1 keep\ntemp2 keep\n...\n"},
    open_file="review.txt",
    cursor_start={"line": 1, "col": 1},
    ideal_keystrokes=":1,4s/temp/perm/g\r:5,8s/temp/perm/gc\rnyny",
    success={"type": "buffer_match", "content": "perm1 keep\nperm2 keep\n...\n"},
    related_theory=["vim-substitute-confirm"],
    objective=["...", "..."],
)
verify_and_write(spec, write=True)   # only touches exercises/confirm-each-one.json if it passes
```

`verify_and_write` drives a real `nvim --headless` instance, feeds it
`ideal_keystrokes`, and compares the actual resulting buffer/cursor
against `success` — plus checks `related_theory` derives to the `tier`
you claimed, and that `par` (computed from your keystrokes, not
hand-set) clears that tier's floor. It prints `[OK]` or `[FAIL]` with the
actual mismatch, and **only writes `exercises/<id>.json` on `[OK]`** — a
failing spec never touches the file. Iterate on the spec dict until it
passes; don't hand-edit the JSON afterward.

To re-check an exercise that's already on disk (has real drift-detection
value — run it after any refactor touching `server/exercises.py`'s tier
model, or periodically as a regression sweep):

```sh
python scripts/verify_exercise.py confirm-each-one
```

This only works for exercises that still have `ideal_keystrokes` in
their JSON — see the next section for the two tiers that don't.

## Professional and genius: written the same way, then made private

Author and verify professional/genius exercises exactly like any other —
`ideal_keystrokes` present, verified via `verify_and_write` above. The
privacy step is separate and automatic: `scripts/gen_all_results.py`
archives every exercise's solution into `private/all_results.md` (and
`private/private_solutions.json`, its backing vault), then strips
`ideal_keystrokes` out of professional/genius exercises' JSON files
specifically — the live app never has the reference path for those two
tiers at all, not just hidden from players in the UI. Run it after
you're done authoring:

```sh
python scripts/gen_all_results.py
```

Don't strip `ideal_keystrokes` yourself by hand — the script also
updates the private vault in the same pass, which is what makes it safe
to run again later without losing anything already archived.

## Before you're done

- Run `scripts/verify_exercise.py <id>` (or `verify_and_write` while
  iterating) — non-negotiable, see above.
- Re-read the exercise against the one rule at the top: is every section
  genuinely different, or did two sections just repeat the same trick
  with different words in the workspace text?
- If it's professional or genius, run `scripts/gen_all_results.py`
  before considering it finished — the PR check below fails if you skip
  this (see next bullet), but do it before pushing, not after.
- Every PR runs `scripts/verify_all_exercises.py` in CI
  (`.github/workflows/verify-exercises.yml`) — the same real-Neovim check
  as `verify_exercise.py`, run over every public exercise, plus a check
  that no professional/genius exercise still has `ideal_keystrokes` sitting
  in `exercises/*.json` unscrubbed. It's the safety net, not the primary
  check — verify locally first; don't rely on CI to find a broken
  exercise for you.
- If you added a `prerequisites` entry, sanity-check it isn't a harder
  tier than the exercise itself (`python3 -c` one-liner, run from the
  repo root):

  ```sh
  python3 -c "
  import sys; sys.path.insert(0, 'server')
  from exercises import list_exercises, DIFFICULTY_TIERS
  exs = {e['id']: e for e in list_exercises()}
  for e in exs.values():
      for p in e['prerequisites']:
          pt, et = exs[p['id']]['difficulty'], e['difficulty']
          if DIFFICULTY_TIERS.index(pt) > DIFFICULTY_TIERS.index(et):
              print('violation:', e['id'], et, 'requires', p['id'], pt)
  "
  ```
