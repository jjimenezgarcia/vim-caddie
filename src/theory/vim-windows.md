# Splitting the window

`:split` and `:vsplit` open a second view onto the same set of buffers
— two windows on screen instead of one, each with its own cursor and
scroll position:

- `:split` — split the window horizontally (new window above)
- `:vsplit` — split the window vertically (new window beside it)
- `Ctrl-w` then `h`/`j`/`k`/`l` — move to the window in that direction
- `Ctrl-w` then `q` — close the current window

Editing a buffer in one window updates it everywhere that buffer is
visible — it's still the same file, just viewed from two places at
once.
