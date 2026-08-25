# Marks

`m` followed by a letter drops an invisible bookmark at the cursor,
which you can jump straight back to later:

- `ma` — set mark `a` at the cursor
- `` `a `` — jump to the exact position of mark `a`
- `'a` — jump to the start of the line mark `a` is on

Marks are per-session and per-letter — setting `mb` doesn't disturb
`ma`, so you can hold several places in a file at once.
