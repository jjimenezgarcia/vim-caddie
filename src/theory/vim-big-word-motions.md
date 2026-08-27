# WORD motions

Vim actually has two motion vocabularies for moving by "a word" —
`w`/`e`/`b` (lowercase) stop at *any* punctuation, but capital
`W`/`E`/`B` only care about whitespace, treating a run of punctuation
and letters glued together as one single WORD:

- `W` — jump to the start of the next WORD (whitespace-delimited)
- `E` — jump to the end of the current/next WORD
- `B` — jump backward to the start of a WORD

On `user@host:8080`, `w` stops four separate times (at `@`, `:`,
`8080`); `W` treats the whole thing as one WORD and jumps straight past
it.
