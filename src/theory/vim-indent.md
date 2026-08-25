# Indenting a line

`>>` and `<<` shift the current line by one shiftwidth, without needing
to place the cursor at the start of the line first:

- `>>` — indent the line
- `<<` — un-indent the line
- `3>>` — indent three lines

Same doubling pattern as `dd`/`yy`/`cc`: the operator (`>` or `<`)
repeated acts on the current line as a whole.
