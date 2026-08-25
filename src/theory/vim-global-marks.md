# Global marks

Lowercase marks (`ma`) only mean something within the file they were
set in — an uppercase mark is a *global* mark, valid across every open
file:

- `mA` — set global mark `A` at the cursor
- `` `A `` — jump straight to it, opening that file first if it isn't
  already the one you're in

Same jump syntax as a regular mark, just capitalized — the capital
letter is what makes it global instead of per-file.
