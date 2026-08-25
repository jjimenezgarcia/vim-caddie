"""Generates the `init.vim` for one session, tailored to that exercise's
permission whitelist. Written into the session's /state dir (not baked into
the Docker image) so editor config changes never need an image rebuild —
only the tool whitelist itself does (see scripts/build_exercise_images.py).

Whether the shell is enabled here is directly tied to whether the
exercise's Docker image variant actually has a shell/tools installed at
all (see permissions.image_tag() in server/exercises.py) — turning 'shell'
on for a pure-editing exercise wouldn't be exploitable on its own (there'd
be nothing but nvim in that image to invoke), but keeping it tied 1:1 to
the whitelist avoids ever having a live mismatch between "shell is on" and
"there's something worth reaching with it".
"""

BASE = r"""
set nocompatible
set noswapfile
set nobackup
set nowritebackup
set noundofile
set shadafile=NONE
set nomodeline
set mouse=
set laststatus=2
set title

" no nvim-generated chatter for the player at all — this is a learning
" tool, not a real editing session; buffer state is read over RPC, never
" from disk, so file-permission-related warnings are meaningless noise
set shortmess=aoOtTIcFWAs
set noreadonly
autocmd BufReadPost,BufNewFile * setlocal noreadonly

" reduce attack surface further: don't let nvim try to spawn interpreter
" host processes for remote plugins (none are installed in any image
" variant anyway, but no reason to let it try)
let g:loaded_python3_provider = 0
let g:loaded_ruby_provider = 0
let g:loaded_perl_provider = 0
let g:loaded_node_provider = 0

" The backend's RPC client needs to connect() to the socket --listen just
" created, but it runs as a different (real, non-sandbox) host uid, and
" this process owns that socket — so only this process can grant that
" access. Safe to make broad because the actual boundary is the
" *directory* (0700 + exactly one ACL entry for this uid — see
" NvimSession.__init__ in server/app.py): no other uid on the host can
" reach this path to find the socket at all. (A pre-granted default ACL on
" the directory was tried first, so this chmod wouldn't be needed — but
" the kernel computes a stricter ACL mask for files created via bind()
" than for ordinary file creation, and silently clamped it to read-only.)
lua << SOCKPERM
pcall(vim.loop.fs_chmod, "/state/nvim.sock", tonumber("777", 8))
SOCKPERM

" Registered here (not via a later RPC call from the backend) so it's live
" from Neovim's very first moment — a player can start typing the instant
" the terminal paints, before the backend's RPC client has even connected
" to /state/nvim.sock, and no edit is missed waiting for that handshake.
" 0 = broadcast to every attached RPC channel that has subscribed
" (see server/app.py's nvim.subscribe call).
autocmd ModeChanged,CursorMoved,CursorMovedI,TextChanged,TextChangedI,TextChangedP *
  \ call rpcnotify(0, 'vim_caddie_state')

" `set shell=/bin/false` (below, for no-whitelist exercises) only stops the
" STRING form of system()/:! — Vim's list-form system()/jobstart() and
" `:terminal {cmd}` bypass 'shell' by design (documented behavior, not a
" bug) and are built into Vim's C core, so they cannot be shadowed or
" disabled from Vimscript at all. What CAN be neutralized from here is
" Lua's process-spawn surface, since os/io/package/vim.loop are just
" mutable Lua tables: os.execute/io.popen call libc system()/popen()
" directly (ignoring 'shell' entirely), package.loadlib loads arbitrary
" native .so code, and vim.loop.spawn is Neovim's own libuv process-spawn
" primitive exposed to Lua. All four are real, tested, working exploit
" paths without this block — kept for every exercise regardless of its
" whitelist, since it's cheap and doesn't affect any legitimate editing.
"
" This is still defense in depth, not a sandbox: jobstart()/list-form
" system()/`:terminal {cmd}` remain unblockable from in here. The actual
" containment for all of this is the container itself (see docker run
" flags in server/app.py) — no network, read-only fs outside /state, all
" capabilities dropped, resource limits, non-root, --rm — plus, now, the
" fact that a no-whitelist exercise's image has no shell and no extra
" tools in it at all, so there is nothing there for any of these to reach.
lua << EOF
os.execute = nil
os.remove = nil
os.rename = nil
os.tmpname = nil
io.popen = nil
package.loadlib = nil
if vim.loop then
  vim.loop.spawn = nil
end
EOF
"""

NO_SHELL = r"""
" no commands whitelisted for this exercise: no shell, netrw off. This
" isn't the primary control (see BASE's note above) — the primary control
" is that this exercise's image genuinely has no shell binary installed —
" but it keeps :!/:terminal's own error message honest ("shell not
" found") instead of a shell existing but being told to lie about running.
set shell=/bin/false
let g:loaded_netrw = 1
let g:loaded_netrwPlugin = 1
"""

WITH_SHELL = r"""
" this exercise's image has a real shell and its whitelisted tools
" installed — :!, :r !cmd, and netrw's file browsing are all meant to
" work here as taught features, not accidents. What makes this safe is
" that the image contains nothing beyond the whitelist, not that the
" shell is disabled.
set shell=/bin/sh
"""


def render_init_vim(commands):
    """commands: the exercise's permissions.commands list (possibly empty)."""
    return BASE + (WITH_SHELL if commands else NO_SHELL)
