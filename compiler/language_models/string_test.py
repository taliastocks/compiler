import unittest

from compiler.language_models import string


class UnescapeTestCase(unittest.TestCase):
    def test_unescape_text_hexadecimal(self):
        self.assertEqual(
            ' \x00 ',
            string.unescape_text(r' \x00 ')
        )
        self.assertEqual(
            ' \x01 ',
            string.unescape_text(r' \x01 ')
        )
        self.assertEqual(
            ' \xff ',
            string.unescape_text(r' \xff ')
        )
        self.assertEqual(
            ' \xFF ',
            string.unescape_text(r' \xFF ')
        )
        self.assertEqual(
            ' \\xa ',
            string.unescape_text(r' \xa ')
        )
        self.assertEqual(
            ' \xabc ',
            string.unescape_text(r' \xabc ')
        )

    def test_unescape_text_character_name(self):
        self.assertEqual(
            ' Ƣ ',
            string.unescape_text(r' \N{LATIN CAPITAL LETTER OI} ')
        )
        self.assertEqual(
            ' 𒋔 ',
            string.unescape_text(r' \N{CUNEIFORM SIGN NU11 TENU} ')
        )
        self.assertEqual(
            ' ࿐ ',
            string.unescape_text(r' \N{TIBETAN MARK BSKA- SHOG GI MGO RGYAN} ')
        )

    def test_unescape_text_unicode_16(self):
        self.assertEqual(
            ' ‼ ',
            string.unescape_text(r' \u203C ')
        )
        self.assertEqual(
            ' ‼ ',
            string.unescape_text(r' \u203c ')
        )

    def test_unescape_text_unicode_32(self):
        self.assertEqual(
            ' 𝌰 ',
            string.unescape_text(r' \U0001D330 ')
        )
        self.assertEqual(
            ' 𝌰 ',
            string.unescape_text(r' \U0001d330 ')
        )

    def test_unescape_text_special_case(self):
        self.assertEqual(
            '\a\b\f\n\r\t\v\"\'',  # final newline is escaped
            string.unescape_text(r'\a\b\f\n\r\t\v\"\'' '\\\n')
        )

    def test_unescape_bytes_hexadecimal(self):
        self.assertEqual(
            b' \x00 ',
            string.unescape_bytes(r' \x00 ')
        )
        self.assertEqual(
            b' \x01 ',
            string.unescape_bytes(r' \x01 ')
        )
        self.assertEqual(
            b' \xff ',
            string.unescape_bytes(r' \xff ')
        )
        self.assertEqual(
            b' \xFF ',
            string.unescape_bytes(r' \xFF ')
        )
        self.assertEqual(
            b' \\xa ',
            string.unescape_bytes(r' \xa ')
        )
        self.assertEqual(
            b' \xabc ',
            string.unescape_bytes(r' \xabc ')
        )

    def test_unescape_bytes_character_name(self):
        self.assertEqual(
            ' Ƣ '.encode('utf8'),
            string.unescape_bytes(r' \N{LATIN CAPITAL LETTER OI} ')
        )
        self.assertEqual(
            ' 𒋔 '.encode('utf8'),
            string.unescape_bytes(r' \N{CUNEIFORM SIGN NU11 TENU} ')
        )
        self.assertEqual(
            ' ࿐ '.encode('utf8'),
            string.unescape_bytes(r' \N{TIBETAN MARK BSKA- SHOG GI MGO RGYAN} ')
        )

    def test_unescape_bytes_unicode_16(self):
        self.assertEqual(
            ' ‼ '.encode('utf8'),
            string.unescape_bytes(r' \u203C ')
        )
        self.assertEqual(
            ' ‼ '.encode('utf8'),
            string.unescape_bytes(r' \u203c ')
        )

    def test_unescape_bytes_unicode_32(self):
        self.assertEqual(
            ' 𝌰 '.encode('utf8'),
            string.unescape_bytes(r' \U0001D330 ')
        )
        self.assertEqual(
            ' 𝌰 '.encode('utf8'),
            string.unescape_bytes(r' \U0001d330 ')
        )

    def test_unescape_bytes_special_case(self):
        self.assertEqual(
            '\a\b\f\n\r\t\v\"\''.encode('utf8'),  # final newline is escaped
            string.unescape_bytes(r'\a\b\f\n\r\t\v\"\'' '\\\n')
        )
