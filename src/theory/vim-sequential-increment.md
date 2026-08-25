# Sequential increment

`Ctrl-a` normally adds the same amount every time — but applied to a
block visual selection with `g` in front, it counts up once per line
instead of repeating the same increment:

- select a column of identical numbers with `Ctrl-v`, then `g Ctrl-a` —
  the first becomes +1, the second +2, the third +3, and so on

It's the standard trick for turning a column of `0`s into a numbered
list in one move, instead of incrementing each line by hand.
