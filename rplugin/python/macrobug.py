import neovim

@neovim.plugin
class MacroBug(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.command('MacroBug', nargs='1')
    def do_command(self, args):
        register_key = args[0]
        if len(register_key) != 1:
            # doesn't seem to work. What do I do wrong here?
            self.vim.out_write('expecting a register as parameter')
            return
        # TODO close any previous MacroBug window
        self.target_win = self.vim.current.window
        self.change_root = self.vim.eval('undotree()')['seq_last']
        if self.change_root is None:
            # TODO: don't raise exception, use out_write
            raise Exception('TODO')
        # TODO in case of exception, unset nomodifiable
        self.vim.command('setlocal nomodifiable')
        # normal! ignores the mapping the user has set up
        # The V before the pasting is used to avoid the creation of a new line
        #  (is there any better solution?
        #   self.vim.eval doesn't seem to work currently)
        self.vim.command('new +normal!\\ V"%cp0' % register_key)
        # TODO ensure the register is only 1-line
        self.buffer = self.vim.current.buffer
        self.window = self.vim.current.window
        self.winnr = self.vim.eval('winnr()')
        self.register_key = register_key
        self.window.height = 2
        self.last_col = self.current_col
        # Cannot register to keypress event yet, do some workaround here.
        self.vim.command('setlocal ut=500')
        self.vim.command(('autocmd CursorMoved,CursorHoldI <buffer=%d> ' +
                          ':call rpcnotify(%d, "cursor_move")') %
                         (self.buffer.number, self.vim.channel_id))

    @property
    def current_col(self):
        return self.window.cursor[1]

    @property
    def macro(self):
        return self.buffer[0]

    @neovim.command('MacroSave')
    def save_register(self):
        if not self.window.valid:
            # TODO don't raise exception
            raise Exception('TODO')
        self.vim.command('let @%c="%s"' % (self.register_key, self.macro))
        self.vim.command('%iwindo q!' % self.winnr)

    def check_cursor_moved(self):
        if self.current_col == self.last_col:
            return False
        self.last_col = self.current_col
        return True

    def run_macro_chunk(self):
        try:
            keys = self.vim.replace_termcodes(self.macro[0:self.current_col + 1])
            self.vim.current.window = self.target_win
            self.vim.command('setlocal modifiable')
            self.vim.command('undo %i' % self.change_root)
            # Important : don't use "normal!" as we want the keymappings
            # Also feedkeys is not what we want: it fails
            # when the user inserts keys in the debugger window.
            self.vim.command('normal %s' % keys)
            self.vim.command('call macrobug#draw_cursor()')
        finally:
            self.vim.command('setlocal nomodifiable')
            self.vim.current.window = self.window

    @neovim.rpc_export('cursor_move')
    def on_cursor_move(self):
        if not self.check_cursor_moved():
            return
        self.run_macro_chunk()
