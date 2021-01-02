def escape_bytes(buffer: bytes) -> str:
    return ''.join(_escapes[c] for c in buffer)


_escapes = [
    chr(c) if 32 <= c < 127 else '\\{:03o}'.format(c)
    for c in range(256)
]
# Special cases (https://en.cppreference.com/w/cpp/language/escape)
_escapes[7] = '\\a'
_escapes[8] = '\\b'
_escapes[9] = '\\t'
_escapes[10] = '\\n'
_escapes[11] = '\\v'
_escapes[12] = '\\f'
_escapes[13] = '\\r'
_escapes[34] = '\\\"'
_escapes[39] = '\\\''
_escapes[63] = '\\?'  # trigraphs
_escapes[92] = '\\\\'
