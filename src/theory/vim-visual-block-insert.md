# Editing multiple lines at once in block mode

Inside a `Ctrl-v` block selection, `I`, `A`, and `c` don't just edit the
block itself — once you press `Esc`, the same edit applies to every
line the block covered:

- select a block with `Ctrl-v`, then `I`, type text, `Esc` — inserts
  that text at the start of the block on every selected line
- same block, `A` instead — appends after the block on every line
- same block, `c` instead — replaces the block's contents on every line

One typed edit, applied down every line of the block simultaneously.
