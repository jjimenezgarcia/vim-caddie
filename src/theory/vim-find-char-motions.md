# Finding a character

`f` and `t` jump forward, along the current line, straight to a
character you name — no counting columns by eye, no repeated `l`:

- `fx` — jump onto the next `x` on the line
- `tx` — jump to just before the next `x` (stops one column short of it)
- `Fx` — same idea, backward: jump onto the previous `x`
- `Tx` — jump to just after the previous `x`, searching backward

- `;` — repeat the last find, same direction
- `,` — repeat the last find, opposite direction

Unlike `w`/`b`, these don't care about word boundaries at all — they
stop on whatever single character you name, punctuation included, and
they never leave the current line.
