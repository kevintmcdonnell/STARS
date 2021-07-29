import re

from constants import WORD_MASK

'''
https://github.com/sbustars/STARS

Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''


# Format an integer as a hexadecimal string (with leading zeros)
def format_hex(x: int) -> str:
    return f'0x{x & WORD_MASK:08x}'


# Handle escape sequences and replace them with the actual characters
def handle_escapes(s: str) -> str:
    escape_seqs = {
        'n': '\n',
        'r': '\r',
        't': '\t',
        '0': '\0',
        '"': '"'
    }

    for escape_char in escape_seqs:
        def replace_func(match):
            # Replace the backslash and the following character with the replacement
            return match.group(0)[:-2] + escape_seqs[escape_char]

        # Match an odd number of backslashes followed by the escape character
        pattern = r'(?<!\\)(\\\\)*\\' + escape_char
        s = re.sub(pattern, replace_func, s)

    # Replace all double backslashes with a single backslash (since \\ is an escape seq for \)
    s = re.sub(r'\\\\', r'\\', s)

    return s


def align_address(address: int, alignment: int):
    '''Return the address padded to fit the alignment given.'''
    mod = address % alignment
    if mod != 0:
        address += (alignment - mod)
    return address