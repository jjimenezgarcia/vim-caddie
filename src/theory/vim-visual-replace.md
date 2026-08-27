# Replacing a whole selection with one character

`r` normally replaces a single character — select something first with
visual mode, then press `r`, and every character in the selection gets
replaced with the same one:

- `v` to select a few characters, then `rx` — every one of them
  becomes `x`

Unlike normal-mode `r`, this doesn't need a one-to-one match between
keystrokes and characters — one selection, one keystroke, the whole
thing changes at once.
