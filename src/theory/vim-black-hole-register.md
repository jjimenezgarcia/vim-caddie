# The black hole register

Prefixing a delete with `"_` sends it to the black hole register
instead of any real one — the deleted text is gone for good, and
nothing already in a register gets overwritten:

- `"_dd` — delete the line without touching any register
- `"_x` — delete a character the same way

Ordinary `dd`/`x` always clobber the default register — this is how to
delete something you don't want, right before pasting something you
saved earlier, without losing it.
