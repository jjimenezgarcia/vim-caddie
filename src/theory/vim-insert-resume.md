# Resuming insert mode

`gi` drops back into insert mode at the exact spot you last left it
from — even if you've moved the cursor somewhere else in the meantime:

- leave insert mode with `Esc`, move around, then `gi` — you're back
  typing right where you stopped, no need to navigate back by hand

Regular `i` always inserts at the *current* cursor position; `gi`
ignores wherever the cursor is now and returns to the last insertion
point instead.
