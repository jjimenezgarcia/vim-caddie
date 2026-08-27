# Substituting a character or line

Two shortcuts for "delete this, then start typing right here" — no
separate delete step first:

- `s` — delete the character under the cursor and drop into insert mode
  (shorthand for `cl`)
- `S` — delete the whole line and drop into insert mode (shorthand for
  `cc`)

Reach for `s` instead of `r` when the replacement isn't a single
character — `r` always swaps exactly one character for exactly one
other, while `s` deletes then lets you type anything, any length.

Don't confuse either of these with `:s`, the Ex command for pattern
substitution — same letter, unrelated command; that one always starts
with a colon.
