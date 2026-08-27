# Reindenting a line

`>>`/`<<` shift a line by a fixed amount — `==` instead lets Vim decide
the correct indent for the line, based on its own indentation rules:

- `==` — reindent the current line
- `3==` — reindent three lines

Where `>>` always adds one more level regardless of what's already
there, `==` corrects the line to whatever indent it *should* have —
useful after moving a line to a different nesting depth.
