import urllib, urllib.request
import json

try:
  import vim
except:
  print("No vim module available outside vim")
  pass


import openai
from AUTH import *

openai.organization = ORGANIZATION_ID
openai.api_key = SECRET_KEY
MAX_SUPPORTED_INPUT_LENGTH = 4096
USE_STREAM_FEATURE = True
MAX_TOKENS_DEFAULT = 64

def complete_input_max_length(input_prompt, max_input_length=MAX_SUPPORTED_INPUT_LENGTH, stop=None, max_tokens=64):
    input_prompt = input_prompt[-max_input_length:]
    response = openai.Completion.create(engine='davinci-codex', prompt=input_prompt, best_of=1, temperature=0.5, max_tokens=max_tokens, stream=USE_STREAM_FEATURE, stop=stop)
    return response

def complete_input(input_prompt, stop, max_tokens):
    try:
        response = complete_input_max_length(input_prompt, int(2.5 * MAX_SUPPORTED_INPUT_LENGTH), stop=stop, max_tokens=max_tokens)
    except openai.error.InvalidRequestError:
        response = complete_input_max_length(input_prompt, MAX_SUPPORTED_INPUT_LENGTH, stop=stop)
        # print('Using shorter input.')

    return response

def get_max_tokens():
    max_tokens = None
    if vim.eval('exists("a:max_tokens")') == '1':
        max_tokens_str = vim.eval('a:max_tokens')
        if max_tokens_str:
            max_tokens = int(max_tokens_str)

    if not max_tokens:
        max_tokens = MAX_TOKENS_DEFAULT

    return max_tokens


def create_completion(stop=None): 
    max_tokens = get_max_tokens()
    vim_buf = vim.current.buffer
    input_prompt = '\n'.join(vim_buf[:])
    
    row, col = vim.current.window.cursor
    input_prompt = '\n'.join(vim_buf[row:])
    input_prompt += '\n'.join(vim_buf[:row-1])
    input_prompt += '\n' + vim_buf[row-1][:col]
    response = complete_input(input_prompt, stop=stop, max_tokens=max_tokens)
    write_response(response, stop=stop)

def write_response(response, stop):
    vim_buf = vim.current.buffer
    vim_win = vim.current.window
    while True:
        if USE_STREAM_FEATURE:
            single_response = next(response)
        else:
            single_response = response
        completion = single_response['choices'][0]['text']
        if stop == '\n':
            completion += '\n'
        row, col = vim.current.window.cursor
        current_line = vim.current.buffer[row-1]
        new_line = current_line[:col] + completion + current_line[col:]
        if not USE_STREAM_FEATURE:
            if new_line == '':
                new_line = new_line
            elif new_line[-1] == '\n':
                new_line = new_line[:-1]
        new_lines = new_line.split('\n')
        new_lines.reverse()
        if len(vim_buf) == row:
            vim_buf.append('')
               
        vim_buf[row-1] = None
        cursor_pos_base = tuple(vim_win.cursor)
        for row_i in range(len(new_lines)):
            vim.current.buffer[row-1:row-1] = [new_lines[row_i]]

        if new_line == '':
            cursor_target_col = 0
        elif new_line[-1] != '\n':
            cursor_target_col = len(new_lines[0])
        else:
            cursor_target_col = 0
        vim_win.cursor = (cursor_pos_base[0] + row_i, cursor_target_col)

        if not USE_STREAM_FEATURE:
            break

        # Flush the vim buffer.
        vim.command("redraw")
        if USE_STREAM_FEATURE:
            if single_response['choices'][0]['finish_reason'] != None: break


def fix_lines():
    # vim get lines currently selected in visual mode.
    vim_buf = vim.current.buffer
    vim_win = vim.current.window
    selected_lines = vim_buf[vim_buf.mark('<')[0]-1:vim_buf.mark('>')[0]]
    # Get the row and col of the visual selection.
    row_start, col_start = vim_buf.mark('<')
    row_end, col_end = vim_buf.mark('>')
    # Print all rows and cols.
    print(row_start, col_start)
    print(row_end, col_end)
    # Print the lines of the selection.
    # print(vim_buf[row_start-1:row_end-1])
    # Print the lines of the selection
    # if len(selected_lines) ==
    wrong_code_block = '\n#' + '\n#'.join(vim_buf[row_start-1:row_end]) 
    input_prompt = '\n'.join(vim_buf[row_end:])
    input_prompt += '\n'.join(vim_buf[:row_start-1])
    input_prompt += '\n# Code containing errors:'
    input_prompt += '\n# ======================='
    input_prompt += wrong_code_block
    input_prompt += '\n# ======================='
    input_prompt += '\n# Fixed code that does the same as above and is not commented out but does not throw errors:'
    input_prompt += '\n# ======================='
    print("input_prompt:", input_prompt)
    response = complete_input(input_prompt, stop=None, max_tokens=len(wrong_code_block)/2)
    row, col = row_start, col_start
    lines_to_insert = []
    while True:
        if not lines_to_insert:
            single_response = next(response)
            completion = single_response['choices'][0]['text']
            lines_to_insert = completion.split('\n')
            print("lines_to_insert:", lines_to_insert)

        # Pop first element from list.
        next_line = lines_to_insert.pop(0)
        if row_end - row >= 0:
            vim_buf[row-1] = next_line
        else:
            vim_buf[row-1:row-1] = [next_line]

        vim.command("redraw")
        if USE_STREAM_FEATURE:
            if single_response['choices'][0]['finish_reason'] != None: break

        row += 1
        # vim_win.cursor = (row + 1, col)
        vim_win.cursor = (row, col)


def fix_line(stop='\n'): 
    vim_buf = vim.current.buffer
    input_prompt = '\n'.join(vim_buf[:])
    
    row, col = vim.current.window.cursor
    input_prompt = '\n'.join(vim_buf[row:])
    input_prompt += '\n'.join(vim_buf[:row-1])
    input_prompt += '\n# Line containing error:'
    input_prompt += '\n#' + vim_buf[row-1]
    input_prompt += '\n# Fixed line that does the same as above and is not uncommented but does not throw an error:'
    input_prompt += '\n'
    if vim_buf[row-1][0] == ' ':
        input_prompt += ' '
        completion_prefix = ' '
    else:
        completion_prefix = ''
    print("input_prompt:", input_prompt)
    response = complete_input(input_prompt, stop=stop, max_tokens=64)
    single_response = next(response)
    completion = single_response['choices'][0]['text']
    vim_buf[row-1] = completion_prefix + completion
