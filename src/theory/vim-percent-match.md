# Jumping to the matching bracket

`%` jumps the cursor from a bracket to whichever one closes or opens it:

- on `(` — `%` jumps to its matching `)`
- on `[` or `{` — `%` jumps to its matching `]` or `}`
- on the closing bracket — `%` jumps back to the opening one

It works from anywhere on the bracket character itself, and combines
with operators like anything else: `d%` deletes from the bracket to its
match.
