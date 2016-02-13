" TODO support highlight overriding
hi macro_bug_cursor  term=reverse cterm=reverse gui=reverse
hi link macro_bug_visual Visual
" Inspired from vim-multiple-cursors
" https://github.com/terryma/vim-multiple-cursors/blob/47c9e3fb11a202a9a2fa1d591ec990a41e4221c4/autoload/multiple_cursors.vim#L811
function! macrobug#draw_cursor()
  let pos = getpos('.')
  if exists('s:cursor_id')
    call matchdelete(s:cursor_id)
  endif
  if exists('s:visual_id')
    call matchdelete(s:visual_id)
    unlet s:visual_id
  endif
  let s:cursor_id = matchadd('macro_bug_cursor', '\%'.pos[1].'l\%'.pos[2].'c', 99999)
  let cur_mode = mode()
  " None of these work. Why?
  if cur_mode ==# 'V'
    call s:quit_visual()
    let s:visual_id = matchadd('macro_bug_visual', '\%>'.(getpos("'<")[1]-1).'l\%<'.(getpos("'>")[1]+1).'l', 99999)
  elseif cur_mode ==# 'v'
    " TODO
    echom "visual"
  else
    echom cur_mode
  endif
endfunction

function s:quit_visual()
  " is there a smarter way to do this?
  exe "normal \<c-c>"
endfunction
