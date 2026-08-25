# Operators on the whole line

Doubling an operator makes it act on the entire current line, instead of
needing an explicit motion:

- `dd` — delete the whole line
- `yy` — yank (copy) the whole line
- `cc` — change the whole line (delete it, then drop into insert mode)

Doubling reads naturally once you know the pattern: the operator is
being told "act on a line's worth," the same way `dw` tells it "act on
a word's worth."
