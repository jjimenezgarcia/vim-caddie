# Operators

An operator is a command that needs something to act on — it doesn't do
anything by itself. The common ones:

- `d` — delete
- `c` — change (delete, then drop into insert mode)
- `y` — yank (copy)

Press one alone and Vim just waits: an operator needs a motion (or a
text object) to tell it *what* to act on.
