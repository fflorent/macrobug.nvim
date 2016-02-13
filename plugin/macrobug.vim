" Some code inspired from vim-multiple-cursors
" https://github.com/terryma/vim-multiple-cursors/blob/47c9e3fb11a202a9a2fa1d591ec990a41e4221c4/autoload/multiple_cursors.vim#L811
" Thanks a lot to this guy and all of the contributors for
" this amazing script!

" TODO support highlight overriding
hi macro_bug_cursor  term=reverse cterm=reverse gui=reverse
hi link macro_bug_visual Visual

function! macrobug#draw_cursor()
  let pos = getpos('.')
  if exists('s:cursor_id')
    call matchdelete(s:cursor_id)
  endif
  if exists('s:visual_ids')
    for id in s:visual_ids
      call matchdelete(id)
    endfor
    unlet s:visual_ids
  endif
  let s:cursor_id = matchadd('macro_bug_cursor', '\%'.pos[1].'l\%'.pos[2].'c', 99999)
  let cur_mode = mode()
  " None of these work. Why?
  if cur_mode ==# 'V' || cur_mode ==# 'v' || cur_mode ==# "\<c-v>"
    call s:quit_visual()
    call s:draw_visual(cur_mode)
  endif
endfunction

function s:quit_visual()
  exe "normal! \<Esc>"
endfunction

function s:draw_visual(mode)
  let vposbegin = getpos("'<")[1:2]
  let vposend = getpos("'>")[1:2]
  let linebegin = vposbegin[0] - 1
  let lineend = vposend[0] + 1
  let pattern = '\%>'.linebegin.'l\%<'.lineend.'l'
  if a:mode !=# 'V'
    let colbegin = min([vposbegin[1], vposend[1]]) - 1
    let colend = max([vposbegin[1], vposend[1]]) + 1
    let pattern .= '\%>'.colbegin.'c'.'\%<'.colend.'c'
  endif
  let s:visual_ids = [matchadd('macro_bug_visual', pattern, 99998)]
  if a:mode ==# 'v'
    let right_content_id = matchadd('macro_bug_visual', '\%>'.linebegin.'l\%>'.(colend - 1).'c\%<'.(lineend-1).'l', 99998)
    let s:visual_ids = add(s:visual_ids, right_content_id)
    let left_content_id = matchadd('macro_bug_visual', '\%>'.(linebegin+1).'l\%<'.(colbegin + 1).'c\%<'.lineend.'l', 99998)
    let s:visual_ids = add(s:visual_ids, left_content_id)
  endif
endfunction

function! macrobug#test()
  call s:draw_visual(visualmode())
endfunction
