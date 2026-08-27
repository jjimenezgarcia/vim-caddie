# Tag text objects

`it`/`at` describe "the contents of this markup tag" as a target for
an operator, the same inner/around pattern as `iw`/`aw` and
parentheses:

- `dit` — delete inside the tag the cursor is inside of, keeping the
  opening and closing tags themselves
- `dat` — delete the whole tag, opening, closing, and everything
  between

Works from anywhere between a matching pair of tags, not just right
next to them — Vim finds the enclosing pair on its own.
