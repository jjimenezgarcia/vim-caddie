# The global command

`:g/pattern/cmd` runs an ex command on every line matching `pattern`,
across the whole file, in one pass:

- `:g/TODO/d` — delete every line containing "TODO"
- `:g/error/normal @a` — on every line containing "error", replay macro
  `a` on that line

It finds all the matching lines first, then runs `cmd` once per line —
combined with a macro, it's how a single recorded edit gets applied
everywhere it's needed without a loop of your own.
