# Fixing a mistake without leaving insert mode

Two keys correct what you just typed without a trip back to normal
mode:

- `Ctrl-w` — delete the word before the cursor
- `Ctrl-u` — delete everything typed since entering insert mode, back
  to the start of the line

Both stay entirely in insert mode — no `Esc`, no operator, just erase
and keep typing.
