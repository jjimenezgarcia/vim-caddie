# Confirming each substitution

Adding `c` to a `:s` or `:%s` command pauses at every match and asks
before replacing it, instead of replacing all of them blindly:

- `:%s/foo/bar/gc` — for every "foo" in the file, ask before replacing

At each match: `y` replaces it, `n` skips it, `a` replaces this one and
every remaining match without asking again, `q` stops entirely.
