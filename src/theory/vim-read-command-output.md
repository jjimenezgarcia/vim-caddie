# Reading command output into the buffer

`:r !cmd` (read) inserts a command's output as new lines right into your
buffer, below the cursor — `:r !date` drops the current date into the
file as text. This is the same `!` mechanism as running a shell command
directly, just paired with `:r` instead of running standalone.
