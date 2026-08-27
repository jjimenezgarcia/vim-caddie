# Copying and moving lines with a command

`:t` (or `:copy`) and `:m` (or `:move`) take a range and a destination
line, and copy or move those lines there in one command — no yanking,
no visual selection:

- `:1t$` — copy line 1 to the end of the file
- `:1m$` — move line 1 to the end of the file
- `:5,10m0` — move lines 5 through 10 to the very start of the file

The destination is just another line reference, so `0` (before the
first line) and `$` (the last line) both work exactly the way they do
in any other range.
