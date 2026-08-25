# Macros

`q` followed by a letter records every keystroke that follows into that
register, until `q` stops it — then `@` replays it:

- `qa` — start recording into register `a`
- ...do anything...
- `q` — stop recording
- `@a` — replay whatever was recorded
- `@@` — replay the same macro again

A macro is just a register holding literal keystrokes — anything you
could type by hand, you can record once and replay any number of times.
