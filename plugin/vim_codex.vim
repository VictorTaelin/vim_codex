if !has("python3")
  echo "vim has to be compiled with +python3 to run this"
  finish
endif

if exists('g:sample_python_plugin_loaded')
    finish
endif


let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

python3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
import plugin
EOF



function! CreateCompletion(max_tokens)
  python3 plugin.create_completion()
endfunction

function! CreateCompletionLine()
  python3 plugin.create_completion(stop='\n')
endfunction

function! FixLine()
  python3 plugin.fix_line()
endfunction

command! -nargs=? CreateCompletion call CreateCompletion(<q-args>)
command! -nargs=0 CreateCompletionLine call CreateCompletionLine()
command! -nargs=0 FixLine call FixLine()

map <Leader>co :CreateCompletion<CR>


let g:sample_python_plugin_loaded = 1
