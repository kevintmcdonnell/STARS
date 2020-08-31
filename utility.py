import re


# Format an integer as a hexadecimal string (with leading zeros)
def format_hex(x: int) -> str:
    return f'0x{x & 0xFFFFFFFF:08x}'


# Handle escape sequences and replace them with the actual characters
def handle_escapes(s: str) -> str:
    s = re.sub(r'\\n', '\n', s)
    s = re.sub(r'\\t', '\t', s)
    s = re.sub(r'\\0', '\0', s)

    return s
