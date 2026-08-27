# Jumping back through where you've been

Vim keeps a history of the cursor positions you've jumped *from* — big
motions like `G`, a search, or a mark all add an entry:

- `Ctrl-o` — jump back to the previous position in that history
- `Ctrl-i` — jump forward again, the opposite direction

It's not the same as undo — nothing about the buffer changes, only
where the cursor goes, letting you dart across the file and get right
back to where you were.
