# Reselecting the last visual selection

`gv` re-selects whatever was last selected in visual mode, exactly as it
was — same lines, same shape (character, line, or block).

- select something, do something else, then `gv` — the old selection is
  back, ready for another operator

Useful any time you need to run a second operation over the same region
without re-selecting it by hand.
