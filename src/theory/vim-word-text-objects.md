# Word text objects

`iw` and `aw` describe "the word here" as a target for an operator,
regardless of where in the word the cursor happens to sit:

- `diw` — delete the word under the cursor, not the surrounding spaces
- `daw` — delete the word under the cursor, plus one surrounding space

This is different from `dw` (delete from the cursor *to* the next word):
`diw`/`daw` grab the whole word no matter where inside it the cursor
lands, which `dw` doesn't — put the cursor mid-word and `dw` only takes
the rest of it.
