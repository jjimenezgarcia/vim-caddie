# Numbered registers

Beyond the named `"a`-`"z` registers, Vim keeps a set of numbered ones
that fill in automatically:

- `"0` — always holds the most recent *yank* specifically
- `"1` — the most recent *delete* (of a whole line or more)
- `"2` through `"9` — older deletes, shifted down one slot each time a
  new one happens

A plain `p` still pastes the default register (whatever was yanked or
deleted most recently, of either kind) — reaching into `"1`, `"2`, and
so on is how you get back something a *later* delete overwrote.
