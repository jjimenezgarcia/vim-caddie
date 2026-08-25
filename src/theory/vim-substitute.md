# Substitute

`:s/old/new/` replaces the first match of `old` with `new` on the
current line:

- `:s/foo/bar/` — replace the first "foo" with "bar" on this line
- `:s/foo/bar/g` — replace every "foo" on this line, not just the first

Without the trailing `g`, only the first match on the line gets
replaced — everything after that flag is a separate idea (searching
across a whole file) worth its own pill.
