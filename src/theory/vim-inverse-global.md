# The inverse global command

`:v/pattern/cmd` is `:g`'s mirror image: it runs `cmd` on every line
that does *not* match `pattern`, instead of every line that does.

- `:v/keep/d` — delete every line that doesn't contain "keep"

Equivalent to `:g!/pattern/cmd` — `:v` is just the shorter, dedicated
name for the same "negate the match" idea.
