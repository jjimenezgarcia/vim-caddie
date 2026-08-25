# More text objects

The "inner/around" pattern from word text objects (`iw`/`aw`) extends to
other shapes too — the cursor just needs to be somewhere inside them:

- `ip` / `ap` — inner/around paragraph
- `i"` / `a"` — inner/around a double-quoted string
- `i(` / `a(` — inner/around parentheses

"Inner" grabs just the contents; "around" grabs the contents plus the
surrounding delimiter (or, for a paragraph, the trailing blank line).
