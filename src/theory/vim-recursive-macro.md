# A macro that calls itself

A macro can invoke itself as its own last step — recorded once, it
then keeps re-triggering itself down the file until a motion inside it
finally fails, at which point that failure stops the whole chain:

- while recording macro `a`, end the recording with `@a` itself — at
  record time the register is still empty, so this does nothing yet;
  it's only once recording stops that `@a` really means "run this
  macro again"
- run it once by hand afterward (`@a`) and it keeps recursing on its
  own, line after line, until a motion like `j` fails at the last line
  and the whole recursion unwinds

One call processes the entire rest of the file — no count, no
guessing how many times to repeat it.
