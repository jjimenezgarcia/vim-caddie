# The expression register

`"=` isn't a place text gets stored — writing to it evaluates a
Vimscript expression on the spot, and whatever it returns becomes the
thing being "pasted":

- in insert mode: `Ctrl-r =` then an expression, then `Enter` —
  inserts the result right where the cursor is
- `"=1+1<CR>p` — evaluates `1+1` and pastes `2`

It's a calculator built into every insert and paste — the only
register whose content isn't something you copied, but something Vim
computes for you.
