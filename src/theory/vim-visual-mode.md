# Visual mode

`v` starts visual mode: move the cursor to grow a selection, then hand
it to an operator instead of the operator needing its own motion:

- `v` — start a character-wise selection
- move with any motion to extend it (`w`, `$`, `j`, …)
- `d` — delete the selection
- `y` — yank the selection

It's the same operators you already know (`d`, `y`, `c`), just fed a
selection you built by eye instead of a motion you typed blind.
