# Marks Vim sets for you

Beyond the marks you set by hand with `m`, Vim automatically drops a
few marks of its own as you work:

- `` `` `` — jump back to the cursor position before the last jump
  (pressing it twice hops back and forth between the two)
- `` `. `` — jump to the position of the last change you made
- `` `[ `` — jump to the start of the last changed or yanked text
- `` `] `` — jump to the end of the last changed or yanked text

Same jump syntax as any other mark — these just fill themselves in
instead of needing an `m` first.
