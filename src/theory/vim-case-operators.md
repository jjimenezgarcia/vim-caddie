# Changing case

`gu`, `gU`, and `g~` are operators like `d` or `c` — they need a motion
or text object to act on, and change the case of whatever that covers:

- `gUiw` — uppercase the word under the cursor
- `guiw` — lowercase the word under the cursor
- `g~iw` — toggle the case of the word under the cursor

Doubling works too, the same way as `dd`: `gUU` (or `guu`, `g~~`)
changes the case of the whole current line.
