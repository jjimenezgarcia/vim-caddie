# Toggling the case of a character

`~` flips the case of the character under the cursor — uppercase
becomes lowercase and back again — and moves the cursor one column to
the right:

- `~` — toggle the case of the character under the cursor
- `3~` — toggle the case of the next three characters

It never enters insert mode and never asks which case to switch to — it
just flips whatever's already there.
