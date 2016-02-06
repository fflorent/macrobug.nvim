hi macro_bug_cursor  term=reverse cterm=reverse gui=reverse
" Inspired from vim-multiple-cursors
" https://github.com/terryma/vim-multiple-cursors/blob/47c9e3fb11a202a9a2fa1d591ec990a41e4221c4/autoload/multiple_cursors.vim#L811
function! macrobug#draw_cursor()
    let pos = getpos('.')
    if exists('s:cursor_id')
      call matchdelete(s:cursor_id)
    endif
    let s:cursor_id = matchadd('macro_bug_cursor', '\%'.pos[1].'l\%'.pos[2].'c', 99999)
endfunction
