import unittest

from . import parser as parser_module

# pylint: disable=too-many-lines, too-many-public-methods


class ParserTestCase(unittest.TestCase):
    def test_line_text(self):
        cursor = parser_module.Cursor(
            lines=[
                'hello',
                'world',
            ]
        )

        self.assertEqual('hello', cursor.line_text())
        self.assertEqual('world', cursor.line_text(1))
        self.assertEqual('', cursor.line_text(2))

    def test_last_line(self):
        cursor = parser_module.Cursor(
            lines=[
                'hello',
                'world',
            ]
        )
        self.assertEqual(1, cursor.last_line)

        cursor = parser_module.Cursor(
            lines=[
                'hello',
            ]
        )
        self.assertEqual(0, cursor.last_line)

        cursor = parser_module.Cursor(
            lines=[]
        )
        self.assertEqual(0, cursor.last_line)

    def test_new_from_symbol_begin_block(self):
        parser = parser_module.Cursor([''] * 20)  # prevent clamping line numbers
        begin_block = parser_module.BeginBlock(
            block_depth=1,
            first_line=12,
            next_line=13,
            first_column=24,
            next_column=25,
        )
        new_cursor = parser.new_from_symbol(begin_block)

        self.assertEqual(
            parser_module.Cursor(
                lines=[''] * 20,
                line=13,
                column=25,
                last_symbol=begin_block,
                block_depth=1,
            ),
            new_cursor
        )

    def test_new_from_symbol_end_block(self):
        cursor = parser_module.Cursor([''] * 20)  # prevent clamping line numbers
        end_block = parser_module.EndBlock(
            block_depth=1,
            first_line=12,
            next_line=13,
            first_column=24,
            next_column=25,
        )
        new_cursor = cursor.new_from_symbol(end_block)

        self.assertEqual(
            parser_module.Cursor(
                lines=[''] * 20,
                line=13,
                column=25,
                last_symbol=end_block,
                block_depth=1,
            ),
            new_cursor
        )

    def test_new_from_symbol_token(self):
        cursor = parser_module.Cursor([''] * 20)  # prevent clamping line numbers
        token = parser_module.BlankLine(
            first_line=12,
            next_line=13,
            first_column=24,
            next_column=25,
        )
        new_cursor = cursor.new_from_symbol(token)

        self.assertEqual(
            parser_module.Cursor(
                lines=[''] * 20,
                line=13,
                column=25,
                last_symbol=token,
                block_depth=0,
            ),
            new_cursor
        )

    def test_new_from_symbol_normal_case(self):
        class MySymbol(parser_module.Symbol):
            @classmethod
            def parse(cls, _):
                return None

        cursor = parser_module.Cursor([])
        symbol = MySymbol()
        new_cursor = cursor.new_from_symbol(symbol)

        self.assertEqual(
            parser_module.Cursor(
                lines=[],
                line=0,
                column=0,
                last_symbol=symbol,
                block_depth=0,
            ),
            new_cursor
        )

    def test_parse_one_symbol(self):
        cursor = parser_module.Cursor([
            ''
        ])
        next_cursor = cursor.parse_one_symbol([
            parser_module.BlankLine,
            parser_module.EndLine,
        ])
        self.assertEqual(
            parser_module.BlankLine(
                first_line=0,
                next_line=1,
                first_column=0,
                next_column=0,
            ),
            next_cursor.last_symbol
        )

        cursor = parser_module.Cursor(
            lines=[
                'foo'
            ],
            column=3,
        )
        next_cursor = cursor.parse_one_symbol([
            parser_module.BlankLine,
            parser_module.EndLine,
        ])
        self.assertEqual(
            parser_module.EndLine(
                first_line=0,
                next_line=1,
                first_column=3,
                next_column=0,
            ),
            next_cursor.last_symbol
        )

    def test_parse_one_symbol_fail(self):
        cursor = parser_module.Cursor(['foo'])

        with self.assertRaisesRegex(parser_module.ParseError, r"expected one of \('\*', Regex\['a'\], EndLine\)"):
            cursor.parse_one_symbol([
                parser_module.Characters['*'],
                parser_module.Regex['a'],
                parser_module.EndLine,
            ], fail=True)

    def test_parse_one_symbol_eat_newlines(self):
        # Test a symbol that eats newlines.
        cursor = parser_module.Cursor(
            lines=[
                '',
                '',
                '',
                'foo',
            ],
        )
        next_cursor = cursor.parse_one_symbol([
            parser_module.Identifier,
        ])
        self.assertEqual(
            parser_module.Identifier(
                first_line=3,
                next_line=3,
                first_column=0,
                next_column=3,
                groups=['foo'],
            ),
            next_cursor.last_symbol
        )

        next_cursor = cursor.parse_one_symbol([
            parser_module.EndLine,  # This one should win.
            parser_module.Identifier,
        ])
        self.assertEqual(
            parser_module.EndLine(
                first_line=0,
                next_line=1,
                first_column=0,
                next_column=0,
            ),
            next_cursor.last_symbol
        )

    def test_parse_one_symbol_no_match(self):
        cursor = parser_module.Cursor(
            lines=[
                'foo'
            ],
        )

        with self.assertRaises(parser_module.NoMatchError):
            cursor.parse_one_symbol([
                parser_module.BlankLine,
                parser_module.EndLine,
            ])

    def test_parse_one_symbol_always(self):
        cursor = parser_module.Cursor(
            lines=[
                'foo'
            ],
        )

        new_cursor = cursor.parse_one_symbol([
            parser_module.BlankLine,
            parser_module.EndLine,
            parser_module.Always,
        ])

        self.assertIsInstance(
            new_cursor.last_symbol,
            parser_module.Always
        )

    def test_parse_one_symbol_recursive_no_match(self):
        class MySymbol(parser_module.Symbol):
            @classmethod
            def parse(cls, cursor):  # noqa
                cursor.parse_one_symbol([  # Should raise NoMatchError
                    parser_module.BeginBlock,
                ])

        cursor = parser_module.Cursor(
            lines=[
                ''
            ],
        )

        with self.assertRaises(parser_module.NoMatchError):
            cursor.parse_one_symbol([
                MySymbol
            ])

        # This case should succeed.
        cursor.parse_one_symbol([
            MySymbol,
            parser_module.BlankLine,  # matches
        ])


class TokenTestCase(unittest.TestCase):
    def test_end_file(self):
        self.assertEqual(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=[],
                )
            ),
            parser_module.Cursor(
                lines=[],
                last_symbol=parser_module.EndFile(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=0,
                ),
            )
        )
        self.assertEqual(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=[''],
                )
            ),
            parser_module.Cursor(
                lines=[''],
                last_symbol=parser_module.EndFile(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=0,
                ),
            )
        )
        self.assertIsNone(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=['foo'],
                )
            )
        )
        self.assertIsNone(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=['foo'],
                    column=2,
                )
            )
        )
        self.assertIsNone(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=['', 'foo'],
                    line=1,
                    column=2,
                )
            )
        )
        self.assertEqual(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=['foo'],
                    column=3,
                )
            ),
            parser_module.Cursor(
                lines=['foo'],
                column=3,
                last_symbol=parser_module.EndFile(
                    first_line=0,
                    next_line=0,
                    first_column=3,
                    next_column=3,
                ),
            )
        )
        self.assertEqual(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=['', 'foo'],
                    line=1,
                    column=3,
                )
            ),
            parser_module.Cursor(
                lines=['', 'foo'],
                line=1,
                column=3,
                last_symbol=parser_module.EndFile(
                    first_line=1,
                    next_line=1,
                    first_column=3,
                    next_column=3,
                ),
            )
        )

    def test_end_file_past_end(self):
        self.assertEqual(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=['foo'],
                    column=10,
                )
            ),
            parser_module.Cursor(
                lines=['foo'],
                column=10,
                last_symbol=parser_module.EndFile(
                    first_line=0,
                    next_line=0,
                    first_column=10,
                    next_column=10,
                ),
            )
        )
        self.assertEqual(
            parser_module.EndFile.parse(
                parser_module.Cursor(
                    lines=['foo'],
                    line=10,
                )
            ),
            parser_module.Cursor(
                lines=['foo'],
                line=1,  # clamped to eof + 1 line
                last_symbol=parser_module.EndFile(
                    first_line=10,
                    next_line=10,
                    first_column=0,
                    next_column=0,
                ),
            )
        )

    def test_blank_line(self):
        self.assertEqual(
            parser_module.BlankLine.parse(
                parser_module.Cursor(
                    lines=[''],
                )
            ),
            parser_module.Cursor(
                lines=[''],
                line=1,
                last_symbol=parser_module.BlankLine(
                    first_line=0,
                    next_line=1,
                    first_column=0,
                    next_column=0,
                ),
            )
        )
        self.assertEqual(
            parser_module.BlankLine.parse(
                parser_module.Cursor(
                    lines=['   '],
                )
            ),
            parser_module.Cursor(
                lines=['   '],
                line=1,
                last_symbol=parser_module.BlankLine(
                    first_line=0,
                    next_line=1,
                    first_column=0,
                    next_column=0,
                ),
            )
        )
        self.assertIsNone(
            parser_module.BlankLine.parse(
                parser_module.Cursor(
                    lines=[' a '],
                )
            )
        )

    def test_end_line(self):
        self.assertEqual(
            parser_module.EndLine.parse(
                parser_module.Cursor(
                    lines=[''],
                )
            ),
            parser_module.Cursor(
                lines=[''],
                line=1,
                last_symbol=parser_module.EndLine(
                    first_line=0,
                    next_line=1,
                    first_column=0,
                    next_column=0,
                ),
            )
        )
        self.assertEqual(
            parser_module.EndLine.parse(
                parser_module.Cursor(
                    lines=['a   '],
                    column=1,
                )
            ),
            parser_module.Cursor(
                lines=['a   '],
                line=1,
                last_symbol=parser_module.EndLine(
                    first_line=0,
                    next_line=1,
                    first_column=1,
                    next_column=0,
                ),
            )
        )
        self.assertEqual(
            parser_module.EndLine.parse(
                parser_module.Cursor(
                    lines=['foo'],
                    column=3,
                )
            ),
            parser_module.Cursor(
                lines=['foo'],
                line=1,
                last_symbol=parser_module.EndLine(
                    first_line=0,
                    next_line=1,
                    first_column=3,
                    next_column=0,
                ),
            )
        )
        self.assertIsNone(
            parser_module.EndLine.parse(
                parser_module.Cursor(
                    lines=['foo'],
                    column=2,
                )
            )
        )

    def test_end_line_eof(self):
        self.assertEqual(
            parser_module.EndLine.parse(
                parser_module.Cursor(
                    lines=[''],
                    line=1,
                )
            ),
            parser_module.Cursor(
                lines=[''],
                line=1,  # clamped to last line + 1
                last_symbol=parser_module.EndLine(
                    first_line=1,
                    next_line=2,
                    first_column=0,
                    next_column=0,
                ),
            )
        )

    def test_begin_block(self):
        self.assertEqual(
            parser_module.BeginBlock.parse(
                parser_module.Cursor(
                    lines=['    '],
                )
            ),
            parser_module.Cursor(
                lines=['    '],
                block_depth=1,
                last_symbol=parser_module.BeginBlock(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=0,
                    block_depth=1,
                ),
            )
        )
        self.assertEqual(
            parser_module.BeginBlock.parse(
                parser_module.Cursor(
                    lines=['        hello'],
                    block_depth=1,
                )
            ),
            parser_module.Cursor(
                lines=['        hello'],
                block_depth=2,
                last_symbol=parser_module.BeginBlock(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=0,
                    block_depth=2,
                ),
            )
        )
        self.assertIsNone(
            parser_module.BeginBlock.parse(
                parser_module.Cursor(
                    lines=['    '],
                    block_depth=1,  # same indentation
                )
            )
        )
        self.assertIsNone(
            parser_module.BeginBlock.parse(
                parser_module.Cursor(
                    lines=['    '],
                    column=1,  # not at beginning of line
                )
            )
        )

    def test_begin_block_tabs(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'other whitespace found'):
            parser_module.BeginBlock.parse(
                parser_module.Cursor(
                    lines=['    \t'],
                    block_depth=1,
                )
            )

    def test_begin_block_remainder(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'extra spaces found'):
            parser_module.BeginBlock.parse(
                parser_module.Cursor(
                    lines=['     '],  # 5 spaces
                    block_depth=1,
                )
            )

    def test_begin_block_over_indented(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'block over-indented'):
            parser_module.BeginBlock.parse(
                parser_module.Cursor(
                    lines=['    ' * 3],
                    block_depth=1,
                )
            )

    def test_end_block(self):
        self.assertEqual(
            parser_module.EndBlock.parse(
                parser_module.Cursor(
                    lines=['    '],
                    block_depth=2,
                )
            ),
            parser_module.Cursor(
                lines=['    '],
                block_depth=1,
                last_symbol=parser_module.EndBlock(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=0,
                    block_depth=1,
                ),
            )
        )
        self.assertEqual(
            parser_module.EndBlock.parse(
                parser_module.Cursor(
                    lines=['        hello'],
                    block_depth=3,
                )
            ),
            parser_module.Cursor(
                lines=['        hello'],
                block_depth=2,
                last_symbol=parser_module.EndBlock(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=0,
                    block_depth=2,
                ),
            )
        )
        self.assertIsNone(
            parser_module.EndBlock.parse(
                parser_module.Cursor(
                    lines=['    '],
                    block_depth=1,  # same indentation
                )
            )
        )
        self.assertIsNone(
            parser_module.EndBlock.parse(
                parser_module.Cursor(
                    lines=['    '],
                    column=1,  # not at beginning of line
                )
            )
        )

    def test_end_block_tabs(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'other whitespace found'):
            parser_module.EndBlock.parse(
                parser_module.Cursor(
                    lines=['    \t'],
                    block_depth=1,
                )
            )

    def test_end_block_remainder(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'extra spaces found'):
            parser_module.EndBlock.parse(
                parser_module.Cursor(
                    lines=['     '],  # 5 spaces
                    block_depth=1,
                )
            )

    def test_end_block_multiple(self):
        self.assertEqual(
            parser_module.EndBlock.parse(
                parser_module.Cursor(
                    lines=['    '],
                    block_depth=3,
                )
            ),
            parser_module.Cursor(
                lines=['    '],
                block_depth=2,  # only decrease depth by one at a time
                last_symbol=parser_module.EndBlock(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=0,
                    block_depth=2,
                ),
            )
        )

    def test_end_block_eof(self):
        self.assertEqual(
            parser_module.EndBlock.parse(
                parser_module.Cursor(
                    lines=['    '],
                    line=1,  # past the end by one line
                    block_depth=1,
                )
            ),
            parser_module.Cursor(
                lines=['    '],
                line=1,
                block_depth=0,  # close final block
                last_symbol=parser_module.EndBlock(
                    first_line=1,
                    next_line=1,
                    first_column=0,
                    next_column=0,
                    block_depth=0,
                ),
            )
        )

    def test_whitespace(self):
        self.assertEqual(
            parser_module.Whitespace.parse(
                parser_module.Cursor(
                    lines=['foo   bar'],
                    column=3,
                )
            ),
            parser_module.Cursor(
                lines=['foo   bar'],
                column=6,
                last_symbol=parser_module.Whitespace(
                    first_line=0,
                    next_line=0,
                    first_column=3,
                    next_column=6,
                ),
            )
        )
        self.assertIsNone(
            parser_module.Whitespace.parse(
                parser_module.Cursor(
                    lines=['foo   bar'],
                    column=2,
                )
            )
        )

    def test_multiline_whitespace(self):
        self.assertEqual(
            parser_module.MultilineWhitespace.parse(
                parser_module.Cursor(
                    lines=['foo   bar'],
                    column=3,
                )
            ),
            parser_module.Cursor(
                lines=['foo   bar'],
                column=6,
                last_symbol=parser_module.MultilineWhitespace(
                    first_line=0,
                    next_line=0,
                    first_column=3,
                    next_column=6,
                ),
            )
        )
        self.assertEqual(
            parser_module.MultilineWhitespace.parse(
                parser_module.Cursor(
                    lines=['foo ', '  ', '    bar'],
                    column=3,
                )
            ),
            parser_module.Cursor(
                lines=['foo ', '  ', '    bar'],
                line=2,
                column=4,
                last_symbol=parser_module.MultilineWhitespace(
                    first_line=0,
                    next_line=2,
                    first_column=3,
                    next_column=4,
                ),
            )
        )
        self.assertIsNone(
            parser_module.Whitespace.parse(
                parser_module.Cursor(
                    lines=['foo   bar'],
                    column=2,
                )
            )
        )

    def test_regex(self):
        self.assertEqual(
            parser_module.Regex['a+'].parse(
                parser_module.Cursor(  # eat newlines and spaces
                    lines=['  ', ' aaaa '],
                )
            ),
            parser_module.Cursor(
                lines=['  ', ' aaaa '],
                line=1,
                column=5,
                last_symbol=parser_module.Regex['a+'](
                    first_line=1,
                    next_line=1,
                    first_column=1,
                    next_column=5,
                    groups=['aaaa'],
                ),
            )
        )
        self.assertIsNone(
            parser_module.Regex['a+'].parse(
                parser_module.Cursor(
                    lines=[' b '],
                )
            )
        )

    def test_regex_capture(self):
        self.assertEqual(
            parser_module.Regex['(b)?a+'].parse(
                parser_module.Cursor(
                    lines=[' aaaa '],
                )
            ),
            parser_module.Cursor(
                lines=[' aaaa '],
                column=5,
                last_symbol=parser_module.Regex['(b)?a+'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=5,
                    groups=['aaaa', None],
                ),
            )
        )
        self.assertEqual(
            parser_module.Regex['(b)?a+'].parse(
                parser_module.Cursor(
                    lines=[' baaa '],
                )
            ),
            parser_module.Cursor(
                lines=[' baaa '],
                column=5,
                last_symbol=parser_module.Regex['(b)?a+'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=5,
                    groups=['baaa', 'b'],
                ),
            )
        )

    def test_regex_boundary(self):
        # A non-word character after a word character ends the token.
        self.assertEqual(
            parser_module.Regex['a+'].parse(
                parser_module.Cursor(
                    lines=[' aa* '],
                )
            ),
            parser_module.Cursor(
                lines=[' aa* '],
                column=3,
                last_symbol=parser_module.Regex['a+'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=3,
                    groups=['aa'],
                ),
            )
        )

        # A word-character after a word character cancels the token.
        self.assertIsNone(
            parser_module.Regex['a+'].parse(
                parser_module.Cursor(
                    lines=[' ab '],
                )
            )
        )
        self.assertIsNone(
            parser_module.Regex['a+'].parse(
                parser_module.Cursor(
                    lines=[' a6 '],
                )
            )
        )

        # A word character after a non-word character ends the token.
        self.assertEqual(
            parser_module.Regex['[*]+'].parse(
                parser_module.Cursor(
                    lines=[' **a '],
                )
            ),
            parser_module.Cursor(
                lines=[' **a '],
                column=3,
                last_symbol=parser_module.Regex['[*]+'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=3,
                    groups=['**'],
                ),
            )
        )

        # A space after a non-word character ends the token.
        self.assertEqual(
            parser_module.Regex['[*]+'].parse(
                parser_module.Cursor(
                    lines=[' ** '],
                )
            ),
            parser_module.Cursor(
                lines=[' ** '],
                column=3,
                last_symbol=parser_module.Regex['[*]+'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=3,
                    groups=['**'],
                ),
            )
        )

        # An end of line ends the token.
        self.assertEqual(
            parser_module.Regex['[*]+'].parse(
                parser_module.Cursor(
                    lines=[' **'],
                )
            ),
            parser_module.Cursor(
                lines=[' **'],
                column=3,
                last_symbol=parser_module.Regex['[*]+'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=3,
                    groups=['**'],
                ),
            )
        )

        # A non-word character after a non-word character ends the token.
        self.assertEqual(
            parser_module.Regex['[*]+'].parse(
                parser_module.Cursor(
                    lines=[' **( '],
                )
            ),
            parser_module.Cursor(
                lines=[' **( '],
                column=3,
                last_symbol=parser_module.Regex['[*]+'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=3,
                    groups=['**'],
                ),
            )
        )

    def test_characters(self):
        self.assertEqual(
            parser_module.Characters['..'].parse(
                parser_module.Cursor(
                    lines=[' .. '],
                )
            ),
            parser_module.Cursor(
                lines=[' .. '],
                column=3,
                last_symbol=parser_module.Characters['..'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=3,
                    groups=['..'],
                ),
            )
        )
        self.assertEqual(
            parser_module.Characters['..'].parse(
                parser_module.Cursor(
                    lines=[' ..a'],
                )
            ),
            parser_module.Cursor(
                lines=[' ..a'],
                column=3,
                last_symbol=parser_module.Characters['..'](
                    first_line=0,
                    next_line=0,
                    first_column=1,
                    next_column=3,
                    groups=['..'],
                ),
            )
        )
        self.assertIsNone(
            parser_module.Characters['..'].parse(
                parser_module.Cursor(
                    lines=[' || '],
                )
            )
        )
        self.assertIsNone(
            parser_module.Characters['await'].parse(
                parser_module.Cursor(
                    lines=[' awaiting '],
                )
            )
        )
        self.assertEqual(
            parser_module.Characters['await'].parse(
                parser_module.Cursor(
                    lines=['await'],
                )
            ),
            parser_module.Cursor(
                lines=['await'],
                column=5,
                last_symbol=parser_module.Characters['await'](
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=5,
                    groups=['await'],
                ),
            )
        )
        self.assertEqual(
            parser_module.Characters['await'].parse(
                parser_module.Cursor(
                    lines=['await('],
                )
            ),
            parser_module.Cursor(
                lines=['await('],
                column=5,
                last_symbol=parser_module.Characters['await'](
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=5,
                    groups=['await'],
                ),
            )
        )

    def test_identifier(self):
        self.assertEqual(
            parser_module.Identifier.parse(
                parser_module.Cursor(
                    lines=['foo1   bar'],
                )
            ),
            parser_module.Cursor(
                lines=['foo1   bar'],
                column=4,
                last_symbol=parser_module.Identifier(
                    first_line=0,  # noqa
                    next_line=0,  # noqa
                    first_column=0,  # noqa
                    next_column=4,  # noqa
                    groups=['foo1'],  # noqa
                ),
            )
        )
        self.assertEqual(
            parser_module.Identifier.parse(
                parser_module.Cursor(
                    lines=['foo   bar42'],
                    column=6,
                )
            ),
            parser_module.Cursor(
                lines=['foo   bar42'],
                column=11,
                last_symbol=parser_module.Identifier(
                    first_line=0,  # noqa
                    next_line=0,  # noqa
                    first_column=6,  # noqa
                    next_column=11,  # noqa
                    groups=['bar42'],  # noqa
                ),
            )
        )
        self.assertEqual(
            parser_module.Identifier.parse(
                parser_module.Cursor(
                    lines=[' foo '],
                )
            ),
            parser_module.Cursor(
                lines=[' foo '],
                column=4,
                last_symbol=parser_module.Identifier(
                    first_line=0,  # noqa
                    next_line=0,  # noqa
                    first_column=1,  # noqa
                    next_column=4,  # noqa
                    groups=['foo'],  # noqa
                ),
            )
        )
        self.assertIsNone(
            parser_module.Identifier.parse(
                parser_module.Cursor(
                    lines=['1foo'],
                )
            )
        )

    def test_string_is_raw_is_binary_is_formatted(self):
        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' rbf"foo" '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=9,  # noqa
                groups=('rbf"foo"', 'rbf', '"', 'foo')  # noqa
            ),
            string
        )
        self.assertIs(True, string.is_raw)
        self.assertIs(True, string.is_binary)
        self.assertIs(True, string.is_formatted)
        self.assertEqual('"', string.quote)
        self.assertEqual('foo', string.content)

        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' fbr"foo" '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=9,  # noqa
                groups=('fbr"foo"', 'fbr', '"', 'foo')  # noqa
            ),
            string
        )
        self.assertIs(True, string.is_raw)
        self.assertIs(True, string.is_binary)
        self.assertIs(True, string.is_formatted)
        self.assertEqual('"', string.quote)
        self.assertEqual('foo', string.content)

        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' "foo" '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=6,  # noqa
                groups=('"foo"', '', '"', 'foo')  # noqa
            ),
            string
        )
        self.assertIs(False, string.is_raw)
        self.assertIs(False, string.is_binary)
        self.assertIs(False, string.is_formatted)
        self.assertEqual('"', string.quote)
        self.assertEqual('foo', string.content)

        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' r"foo" '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=7,  # noqa
                groups=('r"foo"', 'r', '"', 'foo')  # noqa
            ),
            string
        )
        self.assertIs(True, string.is_raw)
        self.assertIs(False, string.is_binary)
        self.assertIs(False, string.is_formatted)
        self.assertEqual('"', string.quote)
        self.assertEqual('foo', string.content)

        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' b"foo" '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=7,  # noqa
                groups=('b"foo"', 'b', '"', 'foo')  # noqa
            ),
            string
        )
        self.assertIs(False, string.is_raw)
        self.assertIs(True, string.is_binary)
        self.assertIs(False, string.is_formatted)
        self.assertEqual('"', string.quote)
        self.assertEqual('foo', string.content)

        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' f"foo" '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=7,  # noqa
                groups=('f"foo"', 'f', '"', 'foo')  # noqa
            ),
            string
        )
        self.assertIs(False, string.is_raw)
        self.assertIs(False, string.is_binary)
        self.assertIs(True, string.is_formatted)
        self.assertEqual('"', string.quote)
        self.assertEqual('foo', string.content)

    def test_string_quote(self):
        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' \'foo\' '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=6,  # noqa
                groups=("'foo'", '', "'", 'foo')  # noqa
            ),
            string
        )
        self.assertEqual("'", string.quote)
        self.assertEqual('foo', string.content)

        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' "foo" '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=6,  # noqa
                groups=('"foo"', '', '"', 'foo')  # noqa
            ),
            string
        )
        self.assertEqual('"', string.quote)
        self.assertEqual('foo', string.content)

    def test_string_escape(self):
        string = parser_module.String.parse(
            parser_module.Cursor(
                lines=[' "foo\\"" '],
            )
        ).last_symbol
        self.assertEqual(
            parser_module.String(
                first_line=0,  # noqa
                next_line=0,  # noqa
                first_column=1,  # noqa
                next_column=8,  # noqa
                groups=('"foo\\""', '', '"', 'foo\\"')  # noqa
            ),
            string
        )
        self.assertEqual('"', string.quote)
        self.assertEqual('foo\\"', string.content)

    def test_multiline_string_lines(self):
        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    ' """First line',
                    '    second line',
                    '    """',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=2,
                first_column=1,
                next_column=7,
                content='First line\nsecond line\n',
                is_raw=False,
                is_binary=False,
            )
        )

        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    ' """',
                    '    First line',
                    '      second line',
                    '    """',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=3,
                first_column=1,
                next_column=7,
                content='First line\n  second line\n',
                is_raw=False,
                is_binary=False,
            )
        )

        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    '"""First line',
                    '    """',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=1,
                first_column=0,
                next_column=7,
                content='First line\n',
                is_raw=False,
                is_binary=False,
            )
        )

        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    '"""First line"""',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=0,
                first_column=0,
                next_column=16,
                content='First line',
                is_raw=False,
                is_binary=False,
            )
        )

    def test_multiline_string_is_raw_is_binary_is_formatted(self):
        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    'rbf"""text"""',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=0,
                first_column=0,
                next_column=13,
                content='text',
                is_raw=True,
                is_binary=True,
                is_formatted=True,
            )
        )

        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    'fbr"""text"""',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=0,
                first_column=0,
                next_column=13,
                content='text',
                is_raw=True,
                is_binary=True,
                is_formatted=True,
            )
        )

        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    'r"""text"""',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=0,
                first_column=0,
                next_column=11,
                content='text',
                is_raw=True,
                is_binary=False,
                is_formatted=False,
            )
        )

        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    'b"""text"""',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=0,
                first_column=0,
                next_column=11,
                content='text',
                is_raw=False,
                is_binary=True,
                is_formatted=False,
            )
        )

        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    'f"""text"""',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=0,
                first_column=0,
                next_column=11,
                content='text',
                is_raw=False,
                is_binary=False,
                is_formatted=True,
            )
        )

        self.assertEqual(
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    '"""text"""',
                ])
            ).last_symbol,
            parser_module.MultilineString(
                first_line=0,
                next_line=0,
                first_column=0,
                next_column=10,
                content='text',
                is_raw=False,
                is_binary=False,
                is_formatted=False,
            )
        )

    def test_multiline_string_nonspace_characters_last_line(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'non-space characters on last line of multiline string'):
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    '"""',
                    'line 2"""',
                ])
            )

    def test_multiline_string_outdented_text(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'out-dented text on multiline string'):
            parser_module.MultilineString.parse(
                parser_module.Cursor([
                    '"""',
                    'line 2',
                    '  """',
                ])
            )


class HelpersTestCase(unittest.TestCase):
    # pylint: disable=protected-access
    def test_measure_block_depth(self):
        self.assertEqual(
            0,
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=['hello'],
                )
            )
        )
        self.assertEqual(
            1,
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=['    hello'],
                )
            )
        )
        self.assertEqual(
            2,
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=['        hello'],
                    block_depth=1,
                )
            )
        )

    def test_measure_block_depth_tabs(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'other whitespace found'):
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=['\thello'],
                )
            )

        with self.assertRaisesRegex(parser_module.IndentationError, 'other whitespace found'):
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=['  \thello'],
                )
            )

    def test_measure_block_depth_remainder(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'extra spaces found'):
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=[' hello'],
                )
            )

        with self.assertRaisesRegex(parser_module.IndentationError, 'extra spaces found'):
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=['     hello'],
                )
            )

    def test_measure_block_depth_over_indented(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'block over-indented'):
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=['        hello'],
                )
            )
        with self.assertRaisesRegex(parser_module.IndentationError, 'block over-indented'):
            parser_module._measure_block_depth(
                parser_module.Cursor(
                    lines=['            hello'],
                    block_depth=1,
                )
            )
