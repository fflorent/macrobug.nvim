''' MacroBug python Module, managing commands and events.'''

import neovim

class MacroBug(object):
    ''' Instance of the Debugger '''
    def __init__(self, vim, register_key):
        self.vim = vim
        if len(register_key) != 1:
            # doesn't seem to work. What do I do wrong here?
            raise MacroBugException('Expecting a register as parameter.' +
                                    ' See :help register')
        self.register_key = register_key
        self.target_win = self.vim.current.window
        # self.target_buf_number = self.vim.current.buffer.number
        self.change_root = self.vim.eval('undotree()')['seq_cur']
        if self.change_root is None:
            raise MacroBugException('Cannot find last sequence of the undotree')
        self.cursor_root = self.target_win.cursor[:]
        self.vim.command('setlocal nomodifiable')
        # normal! ignores the mapping the user has set up
        # The V before the pasting is used to avoid the creation of a new line
        #  (is there any better solution?
        #   self.vim.eval doesn't seem to work currently)
        self.vim.command('new +normal!\\ V"%cp0' % register_key)
        self.buffer = self.vim.current.buffer
        if len(self.buffer) > 1:
            raise MacroBugException('Unexpected carriage return in macro')
        self.window = self.vim.current.window
        self.winnr = self.vim.eval('winnr()')
        self.window.height = 2
        self.last_col = self.current_col
        # Cannot register to keypress event yet, do some workaround here.
        self.vim.command('setlocal ut=500', async=True)
        self.vim.command('setlocal noswapfile', async=True)
        self.vim.command(('autocmd CursorMoved,CursorHoldI <buffer=%d> ' +
                          ':call rpcnotify(%d, "macrobug:cursormove")') %
                         (self.buffer.number, self.vim.channel_id),
                         async=True)
        self.vim.command(('autocmd BufUnload <buffer=%d> ' +
                          ':call rpcnotify(%d, "macrobug:quit")') %
                         (self.buffer.number, self.vim.channel_id),
                         async=True)
        self.vim.command('inoremap <buffer> <cr> <lt>cr>', async=True)
        self.vim.command('call macrobug:draw_cursor_and_visual()', async=True)

    @property
    def current_col(self):
        ''' Get the current column position in the debugger window '''
        return self.window.cursor[1]

    @property
    def macro(self):
        ''' The content of the macro (should be in a single line '''
        return self.buffer[0]

    def save_register(self):
        ''' Handle MacroSave '''
        if not self.window.valid:
            raise MacroBugException('Cannot access debugger window')
        self.vim.command('let @%c="%s"' % (self.register_key, self.macro))
        self.vim.command('%iwindo w' % self.winnr)

    def quit(self):
        ''' Handle MacroQuit '''
        if not self.window or not self.window.valid:
            return
        self.vim.command('%iwindo q!' % self.winnr)

    def check_cursor_moved(self):
        ''' Check whether the cursor moved or not (in normal or insert mode) '''
        if self.current_col == self.last_col:
            return False
        self.last_col = self.current_col
        return True

    def run_macro_chunk(self):
        ''' Run the Macro until the position of the cursor. '''
        try:
            # Get the keys from the beginning to the cursor
            keys_to = self.current_col + 1
            keys = self.vim.replace_termcodes(self.macro[0:keys_to])
            # Run the following commands in the context of the debuggee window
            self.vim.current.window = self.target_win
            # Make the latter modifiable
            self.vim.command('setlocal modifiable')
            # Undo any previous changes made with the debugger.
            self.vim.command('undo %i' % self.change_root)
            # If no modification occurred previously, we still want to get our
            # original position if the cursor moved.
            self.vim.current.window.cursor = self.cursor_root[:]
            # Run the commands.
            # Important : don't use "normal!" as we want the keymappings
            # Also feedkeys is not what we want: it fails
            # when the user inserts keys in the debugger window.
            self.vim.command('normal %s' % keys)
            self.vim.command('call macrobug#draw_cursor_and_visual()')
        finally:
            # Reset the window unmodifiable and focus the debugger window
            self.vim.command('setlocal nomodifiable')
            self.vim.current.window = self.window

    def on_quit(self):
        ''' Handle when the debugger window has just been closed. '''
        if self.window and self.window.valid:
            return
        if not self.target_win or not self.target_win.valid:
            return
        focused_win = self.vim.current.window
        self.vim.current.window = self.target_win
        self.vim.command('setlocal modifiable')
        self.vim.command('undo %i' % self.change_root)
        self.vim.command('call macrobug#unset_cursor_and_visual()')
        self.vim.current.window = focused_win

class MacroBugException(Exception):
    ''' MacroBug exception '''
    pass

@neovim.plugin
class Plugin(object):
    ''' Main module (handling events and managing MacroBug instances) '''
    def __init__(self, vim):
        self.vim = vim
        self.instance = None

    @neovim.command('MacroBug', nargs='1')
    def start_macro_bug(self, args):
        ''' Handle MacroBug command '''
        if self.instance:
            self._echo_error('MacroBug debugger instance already open!')
            return

        try:
            self.instance = MacroBug(self.vim, args[0])
        except MacroBugException as exc:
            self._echo_error(exc)
            if self.instance.window and self.instance.window.valid:
                self.quit()
            else:
                self.on_quit()

    def _echo_error(self, err):
        ''' Display an error '''
        if err is Exception:
            err = err.message
        # TODO Wait, why am I not able to use echoerr???
        self.vim.command('echom "MacroBug Error: %s"' % err, async=True)

    @neovim.command('MacroSave')
    def save_register(self):
        ''' Handle MacroSave '''
        try:
            self.instance.save_register()
        except MacroBugException as exc:
            self._echo_error(exc)

    @neovim.command('MacroQuit')
    def quit(self):
        ''' Handle MacroQuit '''
        self.instance.quit()

    @neovim.rpc_export('macrobug:quit')
    def on_quit(self):
        ''' Handle when the debugger window has just been closed. '''
        self.instance.on_quit()
        self.instance = None

    @neovim.rpc_export('macrobug:cursormove')
    def on_cursor_move(self):
        ''' Handle when the cursor moved '''
        if not self.instance.check_cursor_moved():
            return
        self.instance.run_macro_chunk()
