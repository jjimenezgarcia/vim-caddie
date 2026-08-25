# Substitute across a range

`:s///` on its own only touches the current line — putting `%` in front
runs it over the *whole file* instead:

- `:%s/foo/bar/` — replace the first "foo" on every line
- `:%s/foo/bar/g` — replace every "foo" on every line

`%` is shorthand for "line 1 through the last line" — any other range
(`:5,10s/…`) works the same way, just over fewer lines.
