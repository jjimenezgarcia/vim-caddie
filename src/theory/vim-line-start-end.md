# Jumping within a line

Three motions cover the whole line without ever needing a count:

- `0` — the very first column
- `^` — the first non-blank character
- `$` — the last character

`0` and `^` usually land in the same place, unless the line starts with
leading whitespace.
