import unittest

from . import parser as parser_module


class ParserTestCase(unittest.TestCase):
    def test_line_text(self):
        parser = parser_module.Parser(
            lines=[
                'hello',
                'world',
            ]
        )

        self.assertEqual('hello', parser.line_text())
        self.assertEqual('world', parser.line_text(1))
        self.assertEqual('', parser.line_text(2))

    def test_last_line(self):
        parser = parser_module.Parser(
            lines=[
                'hello',
                'world',
            ]
        )
        self.assertEqual(1, parser.last_line)

        parser = parser_module.Parser(
            lines=[
                'hello',
            ]
        )
        self.assertEqual(0, parser.last_line)

        parser = parser_module.Parser(
            lines=[]
        )
        self.assertEqual(0, parser.last_line)

    def test_new_from_symbol_begin_block(self):
        parser = parser_module.Parser([''] * 20)  # prevent clamping line numbers
        begin_block = parser_module.BeginBlock(
            block_depth=1,
            first_line=12,
            next_line=13,
            first_column=24,
            next_column=25,
        )
        new_parser = parser.new_from_symbol(begin_block)

        self.assertEqual(
            parser_module.Parser(
                lines=[''] * 20,
                line=13,
                column=25,
                last_symbol=begin_block,
                block_depth=1,
            ),
            new_parser
        )

    def test_new_from_symbol_end_block(self):
        parser = parser_module.Parser([''] * 20)  # prevent clamping line numbers
        end_block = parser_module.EndBlock(
            block_depth=1,
            first_line=12,
            next_line=13,
            first_column=24,
            next_column=25,
        )
        new_parser = parser.new_from_symbol(end_block)

        self.assertEqual(
            parser_module.Parser(
                lines=[''] * 20,
                line=13,
                column=25,
                last_symbol=end_block,
                block_depth=1,
            ),
            new_parser
        )

    def test_new_from_symbol_token(self):
        parser = parser_module.Parser([''] * 20)  # prevent clamping line numbers
        token = parser_module.BlankLine(
            first_line=12,
            next_line=13,
            first_column=24,
            next_column=25,
        )
        new_parser = parser.new_from_symbol(token)

        self.assertEqual(
            parser_module.Parser(
                lines=[''] * 20,
                line=13,
                column=25,
                last_symbol=token,
                block_depth=0,
            ),
            new_parser
        )

    def test_new_from_symbol_normal_case(self):
        class MySymbol(parser_module.Symbol):
            @classmethod
            def parse(cls, _):
                return None

        parser = parser_module.Parser([])
        symbol = MySymbol()
        new_parser = parser.new_from_symbol(symbol)

        self.assertEqual(
            parser_module.Parser(
                lines=[],
                line=0,
                column=0,
                last_symbol=symbol,
                block_depth=0,
            ),
            new_parser
        )

    def test_parse_one_of(self):
        parser = parser_module.Parser([
            ''
        ])
        next_parser = parser.parse([
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
            next_parser.last_symbol
        )

        parser = parser_module.Parser(
            lines=[
                'foo'
            ],
            column=3,
        )
        next_parser = parser.parse([
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
            next_parser.last_symbol
        )

    def test_parse_no_match(self):
        parser = parser_module.Parser(
            lines=[
                'foo'
            ],
        )

        with self.assertRaises(parser_module.NoMatchError):
            parser.parse([
                parser_module.BlankLine,
                parser_module.EndLine,
            ])

    def test_parse_always(self):
        parser = parser_module.Parser(
            lines=[
                'foo'
            ],
        )

        new_parser = parser.parse([
            parser_module.BlankLine,
            parser_module.EndLine,
            parser_module.Always,
        ])

        self.assertIsInstance(
            new_parser.last_symbol,
            parser_module.Always
        )

    def test_parse_recursive_no_match(self):
        class MySymbol(parser_module.Symbol):
            @classmethod
            def parse(cls, parser):
                parser.parse([  # Should raise NoMatchError
                    parser_module.BeginBlock,
                ])

        my_parser = parser_module.Parser(
            lines=[
                ''
            ],
        )

        with self.assertRaises(parser_module.NoMatchError):
            my_parser.parse([
                MySymbol
            ])

        # This case should succeed.
        my_parser.parse([
            MySymbol,
            parser_module.BlankLine,  # matches
        ])


class TokenTestCase(unittest.TestCase):
    def test_end_file(self):
        self.assertEqual(
            parser_module.EndFile.parse(
                parser_module.Parser(
                    lines=[],
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=[''],
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo'],
                )
            )
        )
        self.assertIsNone(
            parser_module.EndFile.parse(
                parser_module.Parser(
                    lines=['foo'],
                    column=2,
                )
            )
        )
        self.assertIsNone(
            parser_module.EndFile.parse(
                parser_module.Parser(
                    lines=['', 'foo'],
                    line=1,
                    column=2,
                )
            )
        )
        self.assertEqual(
            parser_module.EndFile.parse(
                parser_module.Parser(
                    lines=['foo'],
                    column=3,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['', 'foo'],
                    line=1,
                    column=3,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo'],
                    column=10,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo'],
                    line=10,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=[''],
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['   '],
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=[' a '],
                )
            )
        )

    def test_end_line(self):
        self.assertEqual(
            parser_module.EndLine.parse(
                parser_module.Parser(
                    lines=[''],
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['a   '],
                    column=1,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo'],
                    column=3,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo'],
                    column=2,
                )
            )
        )

    def test_end_line_eof(self):
        self.assertEqual(
            parser_module.EndLine.parse(
                parser_module.Parser(
                    lines=[''],
                    line=1,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['    '],
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['        hello'],
                    block_depth=1,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['    '],
                    block_depth=1,  # same indentation
                )
            )
        )
        self.assertIsNone(
            parser_module.BeginBlock.parse(
                parser_module.Parser(
                    lines=['    '],
                    column=1,  # not at beginning of line
                )
            )
        )

    def test_begin_block_tabs(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'other whitespace found'):
            parser_module.BeginBlock.parse(
                parser_module.Parser(
                    lines=['    \t'],
                    block_depth=1,
                )
            )

    def test_begin_block_remainder(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'extra spaces found'):
            parser_module.BeginBlock.parse(
                parser_module.Parser(
                    lines=['     '],  # 5 spaces
                    block_depth=1,
                )
            )

    def test_begin_block_over_indented(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'block over-indented'):
            parser_module.BeginBlock.parse(
                parser_module.Parser(
                    lines=['    ' * 3],
                    block_depth=1,
                )
            )

    def test_end_block(self):
        self.assertEqual(
            parser_module.EndBlock.parse(
                parser_module.Parser(
                    lines=['    '],
                    block_depth=2,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['        hello'],
                    block_depth=3,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['    '],
                    block_depth=1,  # same indentation
                )
            )
        )
        self.assertIsNone(
            parser_module.EndBlock.parse(
                parser_module.Parser(
                    lines=['    '],
                    column=1,  # not at beginning of line
                )
            )
        )

    def test_end_block_tabs(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'other whitespace found'):
            parser_module.EndBlock.parse(
                parser_module.Parser(
                    lines=['    \t'],
                    block_depth=1,
                )
            )

    def test_end_block_remainder(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'extra spaces found'):
            parser_module.EndBlock.parse(
                parser_module.Parser(
                    lines=['     '],  # 5 spaces
                    block_depth=1,
                )
            )

    def test_end_block_multiple(self):
        self.assertEqual(
            parser_module.EndBlock.parse(
                parser_module.Parser(
                    lines=['    '],
                    block_depth=3,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['    '],
                    line=1,  # past the end by one line
                    block_depth=1,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo   bar'],
                    column=3,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo   bar'],
                    column=2,
                )
            )
        )

    def test_multiline_whitespace(self):
        self.assertEqual(
            parser_module.MultilineWhitespace.parse(
                parser_module.Parser(
                    lines=['foo   bar'],
                    column=3,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo ', '  ', '    bar'],
                    column=3,
                )
            ),
            parser_module.Parser(
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
                parser_module.Parser(
                    lines=['foo   bar'],
                    column=2,
                )
            )
        )

    def test_identifier(self):
        self.assertEqual(
            parser_module.Identifier.parse(
                parser_module.Parser(
                    lines=['foo1   bar'],
                )
            ),
            parser_module.Parser(
                lines=['foo1   bar'],
                column=4,
                last_symbol=parser_module.Identifier(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=4,
                    identifier='foo1',
                ),
            )
        )
        self.assertEqual(
            parser_module.Identifier.parse(
                parser_module.Parser(
                    lines=['foo   bar42'],
                    column=6,
                )
            ),
            parser_module.Parser(
                lines=['foo   bar42'],
                column=11,
                last_symbol=parser_module.Identifier(
                    first_line=0,
                    next_line=0,
                    first_column=6,
                    next_column=11,
                    identifier='bar42',
                ),
            )
        )
        self.assertEqual(
            parser_module.Identifier.parse(
                parser_module.Parser(
                    lines=[' foo '],
                )
            ),
            parser_module.Parser(
                lines=[' foo '],
                column=4,
                last_symbol=parser_module.Identifier(
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=4,
                    identifier='foo',
                ),
            )
        )
        self.assertIsNone(
            parser_module.Identifier.parse(
                parser_module.Parser(
                    lines=['1foo'],
                )
            )
        )

    def test_characters(self):
        self.assertEqual(
            parser_module.Characters['&&'].parse(
                parser_module.Parser(
                    lines=[' && '],
                )
            ),
            parser_module.Parser(
                lines=[' && '],
                column=3,
                last_symbol=parser_module.Characters['&&'](
                    first_line=0,
                    next_line=0,
                    first_column=0,
                    next_column=3,
                ),
            )
        )
        self.assertIsNone(
            parser_module.Characters['&&'].parse(
                parser_module.Parser(
                    lines=[' || '],
                )
            )
        )


class HelpersTestCase(unittest.TestCase):
    # pylint: disable=protected-access
    def test_measure_block_depth(self):
        self.assertEqual(
            0,
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=['hello'],
                )
            )
        )
        self.assertEqual(
            1,
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=['    hello'],
                )
            )
        )
        self.assertEqual(
            2,
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=['        hello'],
                    block_depth=1,
                )
            )
        )

    def test_measure_block_depth_tabs(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'other whitespace found'):
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=['\thello'],
                )
            )

        with self.assertRaisesRegex(parser_module.IndentationError, 'other whitespace found'):
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=['  \thello'],
                )
            )

    def test_measure_block_depth_remainder(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'extra spaces found'):
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=[' hello'],
                )
            )

        with self.assertRaisesRegex(parser_module.IndentationError, 'extra spaces found'):
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=['     hello'],
                )
            )

    def test_measure_block_depth_over_indented(self):
        with self.assertRaisesRegex(parser_module.IndentationError, 'block over-indented'):
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=['        hello'],
                )
            )
        with self.assertRaisesRegex(parser_module.IndentationError, 'block over-indented'):
            parser_module._measure_block_depth(
                parser_module.Parser(
                    lines=['            hello'],
                    block_depth=1,
                )
            )
