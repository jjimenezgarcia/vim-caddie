# Sorting lines

`:sort` reorders lines alphabetically — by default the whole file,
or just a range if one is given:

- `:sort` — sort every line in the file
- `:sort!` — sort in reverse
- `:sort u` — sort and drop duplicate lines
- `:'<,'>sort` — sort only the visually selected lines

It's an ex command like any other, so a line range in front of it
scopes what gets sorted the same way it scopes `:d` or `:s`.
