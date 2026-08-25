# Repeating the last change

`.` repeats the last change you made — not the last motion, the last
thing that actually edited the buffer:

- make any edit (`dw`, `ciw`, `x`, …)
- `.` — do that exact same edit again, wherever the cursor is now

Move somewhere else first and `.` still repeats it there — it's one of
the highest-leverage single keys in Vim, because it turns any edit into
a reusable action.
