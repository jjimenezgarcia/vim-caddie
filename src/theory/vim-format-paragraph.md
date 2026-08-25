# Reflowing a paragraph

`gq` is an operator that rewraps text to fit within `'textwidth'
columns, breaking and joining lines as needed — it doesn't just
truncate, it reflows.

- `:set textwidth=40` — tell Vim how wide a line should be
- `gqip` — reflow the paragraph under the cursor to that width
- `gqq` — reflow just the current line (doubled, same pattern as `dd`)

Nothing happens without a `textwidth` set first — that's what `gq`
wraps *to*.
