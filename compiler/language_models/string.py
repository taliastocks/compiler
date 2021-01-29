import unicodedata

import regex


def unescape_text(escaped: str) -> str:
    return _escape_regex_text.sub(
        _unescape_text,
        escaped
    )


def unescape_bytes(escaped: str) -> bytes:
    return _escape_regex_bytes.sub(
        _unescape_bytes,
        escaped.encode('utf8')
    )


def _unescape_text(match):
    hexadecimal, character_name, unicode_16, unicode_32, special_case = match.groups()

    if hexadecimal:
        return chr(int(hexadecimal, 16))

    if character_name:
        return unicodedata.lookup(character_name)

    if unicode_16:
        return chr(int(unicode_16, 16))

    if unicode_32:
        return chr(int(unicode_32, 16))

    if special_case:
        return _special_case_escapes_text.get(special_case, special_case)


def _unescape_bytes(match):
    hexadecimal, character_name, unicode_16, unicode_32, special_case = match.groups()

    if hexadecimal:
        return bytes([int(hexadecimal, 16)])

    if character_name:
        return unicodedata.lookup(character_name).encode('utf8')

    if unicode_16:
        return chr(int(unicode_16, 16)).encode('utf8')

    if unicode_32:
        return chr(int(unicode_32, 16)).encode('utf8')

    if special_case:
        return _special_case_escapes_bytes.get(special_case, special_case)


_special_case_escapes_text = {
    r'\a': '\a',
    r'\b': '\b',
    r'\f': '\f',
    r'\n': '\n',
    r'\r': '\r',
    r'\t': '\t',
    r'\v': '\v',
    r'\"': '\"',
    r'\'': '\'',
    r'\\': '\\',
    '\\\n': '',
}
_special_case_escapes_bytes = {
    _key.encode('utf8'): _val.encode('utf8')
    for _key, _val in _special_case_escapes_text.items()
}
_escape_regex_str = (
    r'\\x([0-9a-fA-F]{2})|' +  # hex
    r'\\N{([A-Z0-9\- ]+)}|' +  # unicode character names
    r'\\u([0-9a-fA-F]{4})|' +  # 16-bit unicode
    r'\\U([0-9a-fA-F]{8})|' +  # 32-bit unicode
    r'({})'.format(  # special cases
        '|'.join(
            regex.escape(_key)
            for _key in _special_case_escapes_text.keys()
        )
    )
)
_escape_regex_text = regex.compile(_escape_regex_str)
_escape_regex_bytes = regex.compile(_escape_regex_str.encode('utf8'))
