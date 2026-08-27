# Pasting and moving past it

`gp` and `gP` paste exactly like `p` and `P`, with one difference: the
cursor ends up just *after* what was pasted instead of on its first
character:

- `gp` — paste after the cursor, cursor lands past the pasted text
- `gP` — paste before the cursor, cursor lands past the pasted text

Handy when you're about to paste the same thing again right after —
the cursor's already in position for the next `p`.
