import textwrap
import unittest

from . import tokenizer as tokenizer_module


class TokenizerTestCase(unittest.TestCase):
    def test_init_lines(self):
        tokenizer = tokenizer_module.Tokenizer(
            textwrap.dedent(
                """\
                a
                bunch
                of
                lines
                """
            )
        )

        self.assertEqual(
            (
                "a",
                "bunch",
                "of",
                "lines",
            ),
            tokenizer.lines
        )
