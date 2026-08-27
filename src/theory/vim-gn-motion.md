# Selecting the next search match

`gn` selects the next match of the last search pattern as if it were a
text object — it doesn't just jump to it the way `n` does, it selects
it, ready for an operator:

- `/pattern` then `gn` — visually selects the next match
- `cgn` — change the next match: deletes it and drops into insert mode
  right there

Because `cgn` is one self-contained edit, `.` repeats it on the match
after that — search once, then `cgn`, `.`, `.` fixes every occurrence
one at a time without re-selecting anything.
