# Replacing a single character

`r` followed by one character swaps whatever's under the cursor for
that character, without ever entering insert mode:

- `rx` — replace the character under the cursor with `x`

It's a single atomic edit — no `Esc` needed afterward, since `r` never
actually leaves normal mode.
