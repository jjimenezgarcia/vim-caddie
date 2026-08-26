# How to write a theory pill

"Theory pills" are the small markdown files under `src/theory/*.md`,
shown at the top of an exercise (see `TheorySection.jsx`) for whatever
concepts that exercise's ideal solution depends on. This document is
guidance for writing them — it is not itself a pill, and deliberately
does not live in `src/theory/` (anything there gets picked up by
`theory.js`'s glob import and becomes a real, selectable topic).

## The core idea: reusable, atomic units of knowledge

A pill is not exercise-specific documentation. It's a small, standalone
fact or mechanic that's true regardless of which exercise happens to be
open. The test for "is this one pill or two": could a *different*,
not-yet-written exercise plausibly need one of these ideas without the
other? If yes, they're separate pills.

This is why `src/theory/` currently has `vim-word-motions.md`,
`vim-operators.md`, and `vim-operators-and-motions.md` as three separate
files instead of one — an exercise that's purely "move the cursor to
this word" only needs word motions, not operators at all. Composing them
is its own idea on top of both, and gets its own pill. Same reasoning
split `vim-shell-commands.md` (`:!cmd`) from
`vim-read-command-output.md` (`:r !cmd`) — related, but independently
useful.

## Rules

1. **Never reference a specific exercise.** No exercise's actual
   filenames, starting text, or scenario. Examples should read as
   generic illustrations, not "the answer to exercise X." (Concretely:
   nothing in a pill should look out of place if you didn't know which
   exercise pulled it in.)

2. **One concept per pill, and don't duplicate what another pill already
   owns.** If concept A is explained in `pill-a.md`, `pill-b.md` should
   build on top of it, not re-explain it. An exercise that needs both
   just lists both in its `related_theory`.

3. **Be short.** A pill is a pill, not an article — a sentence or two of
   framing plus a handful of bullets is usually enough. If it's getting
   long, it's probably two pills.

4. **Explanatory text always comes before the example**, never after and
   never interleaved awkwardly. Ground the idea, then show it.

5. **Always include at least one concrete example.** Abstract
   description alone isn't enough — every pill should show, not just tell.

6. **Individual examples are independent inline code, not a fenced code
   block.** A list of short things (`` `w` ``, `` `dw` ``, `` `:!ls` ``)
   should be bullet points with inline code, one per line — not all
   crammed into one ` ``` ` block. Reserve fenced blocks for content
   that's genuinely multi-line and can't be meaningfully split (there's
   no current pill that needs one — that should be rare).

## Mechanics

- File lives at `src/theory/<topic-id>.md`. `<topic-id>` (the filename,
  no extension) is what an exercise's `exercise.json` references in its
  `related_theory` array — pick a clear, descriptive kebab-case id.
- The pill's **title** is whatever text follows the first `# ` heading —
  `theory.js` extracts it from there and strips it out of the rendered
  body, so don't repeat the title as the first line of body text.
- That's the entire format. No frontmatter, no metadata block.

## Example of a correctly-scoped pill

`src/theory/vim-operators.md` in full:

```
# Operators

An operator is a command that needs something to act on — it doesn't do
anything by itself. The common ones:

- `d` — delete
- `c` — change (delete, then drop into insert mode)
- `y` — yank (copy)

Press one alone and Vim just waits: an operator needs a motion (or a
text object) to tell it *what* to act on.
```

Notice what it does *not* do: it doesn't explain word motions (that's
`vim-word-motions.md`'s job), and it doesn't explain how operators
combine with motions (that's `vim-operators-and-motions.md`'s job). It
just answers "what is an operator" — nothing more.
