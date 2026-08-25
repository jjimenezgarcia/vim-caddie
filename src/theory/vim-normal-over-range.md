# Running normal-mode commands over a range

`:normal` takes whatever follows it and runs it as literal normal-mode
keystrokes — prefixed with a range, it runs them once per line in that
range:

- `:'<,'>normal A;` — on every visually selected line, append `;` at
  the end
- `:g/TODO/normal I* ` — on every line matching "TODO", insert `* ` at
  the start

It's how a small edit becomes "do this to every line that qualifies,"
without recording a macro just to replay it with `:g`.
