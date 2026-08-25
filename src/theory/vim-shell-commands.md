# Running shell commands from Vim

You don't have to leave the editor to run a command. Prefix any Ex
command with `!` to hand it to the shell:

- `:!ls` — run `ls`, show the output, then return to your buffer
- `:!cat somefile.txt` — same idea, for reading a file without opening it

Both stay entirely within normal mode's command line — no need to switch
to a separate terminal and back.
