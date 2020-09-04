import re
from constants import WORD_MASK


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
