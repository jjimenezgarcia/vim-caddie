# A few regex basics

Search and substitute patterns aren't limited to literal text — a
handful of special characters cover most everyday cases:

- `^` — matches the start of a line
- `$` — matches the end of a line
- `\d` — matches a single digit

`:s/^/# /` prefixes the current line with `# `; `:%s/\d\+/N/g` replaces
every run of digits in the file with `N` (`\+` means "one or more of the
previous atom").
