# Pasting a register while typing

`Ctrl-r` followed by a register letter inserts that register's content
right into the middle of whatever you're typing, without leaving
insert mode:

- `Ctrl-r a` — insert the contents of register `a` at the cursor
- `Ctrl-r "` — insert the default register (whatever was last yanked
  or deleted)

Same registers `p`/`P` paste from in normal mode — this is just how to
reach them without a trip out of insert mode first.
