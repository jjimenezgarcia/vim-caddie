# Named registers

Prefixing a yank, delete, or paste with `"` and a letter targets a
specific register instead of the default one:

- `"ayy` — yank the line into register `a`
- `"ap` — paste from register `a`
- `"0p` — paste from register `0`, which always holds the *last yank*
  specifically (unaffected by deletes, unlike the default register)

Each letter is its own slot, so you can hold several separate snippets
at once instead of the next yank overwriting the last.
