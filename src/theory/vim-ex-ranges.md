# Ex command ranges

Any `:` command can be prefixed with a line range, telling it which
lines to act on instead of just the current one:

- `:5,10d` — delete lines 5 through 10
- `:.,$d` — delete from the current line (`.`) to the last line (`$`)
- `:'<,'>d` — delete whatever's currently visually selected (Vim fills
  this in automatically when a command is typed from visual mode)

The range comes first, the command comes after — `%` (the whole file)
is just the most common range, not a special case of this.
