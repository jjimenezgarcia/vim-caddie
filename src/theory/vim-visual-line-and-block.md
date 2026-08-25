# Visual line and block mode

Two more ways into visual selection, each shaped differently from plain
`v`:

- `V` — select whole lines at a time, growing by line instead of by
  character
- `Ctrl-v` — select a rectangular block, independent of line length

Once selected, the same operators apply as always (`d`, `y`, `c`) — what
changes is the *shape* of what gets handed to them, not what you do with
it once it's selected.
