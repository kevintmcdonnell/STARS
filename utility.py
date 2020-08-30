# Format an integer as a hexadecimal string (with leading zeros)
def format_hex(x: int) -> str:
    return f'0x{x & 0xFFFFFFFF:08x}'

