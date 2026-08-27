# Jumping backward to the end of a word

`b` jumps backward to the *start* of a word — `ge` jumps backward to
the *end* of one instead, landing on the last character of whatever
word comes before the cursor:

- `ge` — jump backward to the end of the previous word
- `gE` — same, but WORD-wise (whitespace-delimited, like `W`/`E`/`B`)

It fills in the one direction/landing combination `w`/`e`/`b` don't
cover on their own.
