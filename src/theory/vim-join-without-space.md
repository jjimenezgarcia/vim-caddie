# Joining lines without a space

`J` joins the current line with the next, inserting a space at the
seam — `gJ` does the same join but leaves the seam exactly as-is, with
no space added:

- `gJ` — join this line and the next, with nothing inserted between
  them
- `3gJ` — join three lines together the same way

Reach for `gJ` when the line already ends exactly where you want the
join to happen, and an extra space would be wrong.
