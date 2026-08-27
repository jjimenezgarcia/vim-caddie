# Appending to a macro

Recording into a register with a capital letter appends to whatever
that register already holds, instead of overwriting it:

- `qa...q` — record macro `a` from scratch
- `qA...q` — record more keystrokes onto the *end* of macro `a`,
  keeping what was already there

Useful for building a macro up in stages, or patching one more step
onto a macro you already recorded without redoing the whole thing.
