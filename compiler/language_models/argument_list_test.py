import unittest

from . import argument_list, expression as expression_module, namespace as namespace_module
from ..libs import parser as parser_module


class ArgumentListTestCase(unittest.TestCase):
    def test_unpack_values(self):
        arg_list: argument_list.ArgumentList = argument_list.ArgumentList.parse(  # noqa
            parser_module.Cursor(['a, b, c'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        arg_list.unpack_values(
            ['A', 'B', 'C'],
            {},
            namespace,
        )
        self.assertEqual(
            {
                'a': 'A',
                'b': 'B',
                'c': 'C',
            },
            namespace.declarations
        )

        namespace = namespace_module.Namespace()
        arg_list.unpack_values(
            ['A', 'B'],
            {'c': 'C'},
            namespace,
        )
        self.assertEqual(
            {
                'a': 'A',
                'b': 'B',
                'c': 'C',
            },
            namespace.declarations
        )

        namespace = namespace_module.Namespace()
        with self.assertRaisesRegex(TypeError, "no value for parameter 'c'"):
            arg_list.unpack_values(
                ['A', 'B'],
                {},
                namespace,
            )
        with self.assertRaisesRegex(TypeError, "no value for parameter 'c'"):
            arg_list.unpack_values(
                ['A'],
                {'b': 'B'},
                namespace,
            )
        with self.assertRaisesRegex(TypeError, "too many positional arguments: expected 3, got 4"):
            arg_list.unpack_values(
                ['A', 'B', 'C', 'D'],
                {},
                namespace,
            )
        with self.assertRaisesRegex(TypeError, r"unexpected keyword argument\(s\): d, e"):
            arg_list.unpack_values(
                ['A', 'B', 'C'],
                {'d': 'D', 'e': 'E'},
                namespace,
            )

    def test_unpack_values_default(self):
        arg_list: argument_list.ArgumentList = argument_list.ArgumentList.parse(  # noqa
            parser_module.Cursor(['a, b=a, c=1'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        arg_list.unpack_values(
            ['A', 'B', 'C'],
            {},
            namespace,
        )
        self.assertEqual(
            {
                'a': 'A',
                'b': 'B',
                'c': 'C',
            },
            namespace.declarations
        )

        namespace = namespace_module.Namespace()
        arg_list.unpack_values(
            ['A'],
            {},
            namespace,
        )
        self.assertEqual(
            {
                'a': 'A',
                'b': 'A',
                'c': 1,
            },
            namespace.declarations
        )

    def test_parse_positional_keyword(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['a, b, c'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=True,
                    is_keyword=True,
                ),
                argument_list.Argument(
                    expression_module.Variable('b'),
                    is_positional=True,
                    is_keyword=True,
                ),
                argument_list.Argument(
                    expression_module.Variable('c'),
                    is_positional=True,
                    is_keyword=True,
                ),
            ])
        )

    def test_parse_positional_only(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['a, b, /'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=True,
                    is_keyword=False,
                ),
                argument_list.Argument(
                    expression_module.Variable('b'),
                    is_positional=True,
                    is_keyword=False,
                ),
            ])
        )

    def test_parse_keyword_only(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['*, a, b'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=False,
                    is_keyword=True,
                ),
                argument_list.Argument(
                    expression_module.Variable('b'),
                    is_positional=False,
                    is_keyword=True,
                ),
            ])
        )

    def test_parse_positional_only_keyword_only(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['a, /, b, *, c'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=True,
                    is_keyword=False,
                ),
                argument_list.Argument(
                    expression_module.Variable('b'),
                    is_positional=True,
                    is_keyword=True,
                ),
                argument_list.Argument(
                    expression_module.Variable('c'),
                    is_positional=False,
                    is_keyword=True,
                ),
            ])
        )

    def test_parse_extra_positional(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['*a'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=True,
                    is_keyword=False,
                    is_extra=True,
                ),
            ])
        )

    def test_parse_extra_keyword(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['**a'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=False,
                    is_keyword=True,
                    is_extra=True,
                ),
            ])
        )

    def test_parse_multiple_extra_positional(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'multiple "extra positional" arguments found'):
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['*a, *b'])
            )

    def test_parse_multiple_begin_keyword_only(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'multiple "begin keyword-only" markers found'):
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['*, *'])
            )

    def test_parse_multiple_extra_keyword(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'multiple "extra keyword" arguments found'):
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['**a, **b'])
            )

    def test_parse_multiple_end_position_only(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'multiple "end position-only" markers found'):
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['/, /'])
            )

    def test_end_position_only_after_begin_keyword_only(self):
        with self.assertRaisesRegex(parser_module.ParseError,
                                    '"end position-only" marker found after "begin keyword-only" marker'):
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['*, /'])
            )

    def test_parse_variable_initializer(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['a=b'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable(
                        'a',
                        initializer=expression_module.Variable('b'),
                    ),
                    is_positional=True,
                    is_keyword=True,
                ),
            ])
        )

    def test_parse_variable_annotations(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['a: b'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable(
                        'a',
                        annotation=expression_module.Variable('b'),
                    ),
                    is_positional=True,
                    is_keyword=True,
                ),
            ])
        )

    def test_parse_variable_no_annotations(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['a: b']),
                parse_annotations=False,
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable(
                        'a',  # parsing stopped at the ":"
                    ),
                    is_positional=True,
                    is_keyword=True,
                ),
            ])
        )

    def test_parse_expected_variable(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected Variable'):
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['**'])
            )

    def test_parse_trailing_comma(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['a, b,'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=True,
                    is_keyword=True,
                ),
                argument_list.Argument(
                    expression_module.Variable('b'),
                    is_positional=True,
                    is_keyword=True,
                ),
            ])
        )

    def test_parse_multiple_lines(self):
        self.assertEqual(
            argument_list.ArgumentList.parse(
                parser_module.Cursor(['a,', 'b'])
            ).last_symbol,
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=True,
                    is_keyword=True,
                ),
                argument_list.Argument(
                    expression_module.Variable('b'),
                    is_positional=True,
                    is_keyword=True,
                ),
            ])
        )

    def test_check_arguments(self):
        with self.assertRaisesRegex(ValueError, 'multiple "extra positional" arguments not allowed'):
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_positional=True,
                    is_extra=True,
                ),
                argument_list.Argument(
                    expression_module.Variable('b'),
                    is_positional=True,
                    is_extra=True,
                ),
            ])

        with self.assertRaisesRegex(ValueError, 'multiple "extra keyword" arguments not allowed'):
            argument_list.ArgumentList([
                argument_list.Argument(
                    expression_module.Variable('a'),
                    is_keyword=True,
                    is_extra=True,
                ),
                argument_list.Argument(
                    expression_module.Variable('b'),
                    is_keyword=True,
                    is_extra=True,
                ),
            ])


class ArgumentTestCase(unittest.TestCase):
    def test_check_is_keyword_or_is_positional(self):
        with self.assertRaisesRegex(ValueError, 'all arguments must be positional or keyword or both'):
            argument_list.Argument(
                variable=expression_module.Variable('foo'),
                is_positional=False,
                is_keyword=False,
                is_extra=False,
            )

        with self.assertRaisesRegex(ValueError, 'all arguments must be positional or keyword or both'):
            argument_list.Argument(
                variable=expression_module.Variable('foo'),
                is_positional=False,
                is_keyword=False,
                is_extra=True,
            )

        # Should not raise.
        argument_list.Argument(
            variable=expression_module.Variable('foo'),
            is_positional=True,
            is_keyword=False,
            is_extra=False,
        )
        argument_list.Argument(
            variable=expression_module.Variable('foo'),
            is_positional=False,
            is_keyword=True,
            is_extra=False,
        )

    def test_check_is_extra(self):
        # Extra args cannot be both positional and keyword.
        with self.assertRaisesRegex(ValueError, '"extra" arguments cannot be both positional and keyword'):
            argument_list.Argument(
                variable=expression_module.Variable('foo'),
                is_positional=True,
                is_keyword=True,
                is_extra=True,
            )
