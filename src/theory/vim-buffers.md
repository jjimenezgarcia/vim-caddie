# Switching files

`:e` opens another file into a new buffer without leaving Vim; once more
than one is open, `:bn`/`:bp` step between them:

- `:e otherfile.txt` — open (or switch to) that file
- `:bn` — switch to the next open buffer
- `:bp` — switch to the previous open buffer

Every open file keeps its own cursor position and undo history, even
while you're looking at a different one.
