import decimal
import unittest
from unittest import mock

from . import expression as expression_module, argument_list, namespace as namespace_module
from ..libs import parser as parser_module

# pylint: disable=fixme
# pylint: disable=too-many-lines


class NumberTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertEqual(
            decimal.Decimal('-12.34e-56'),
            expression_module.Number(
                decimal.Decimal('-12.34e-56')
            ).execute(namespace_module.Namespace())
        )

    def test_parse_float(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12.34e-56'])
            ).last_symbol,
            expression_module.Number(
                decimal.Decimal('12.34e-56')
            )
        )

    def test_parse_integer(self):
        number: expression_module.Number = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['1234'])
        ).last_symbol

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['1234'])
            ).last_symbol,
            expression_module.Number(1234)
        )
        self.assertEqual(
            int,
            type(number.value)
        )

    def test_parse_float_no_magnitude(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12.34'])
            ).last_symbol,
            expression_module.Number(
                decimal.Decimal('12.34')
            )
        )

    def test_parse_integer_magnitude(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12e34'])
            ).last_symbol,
            expression_module.Number(
                decimal.Decimal('12e34')
            )
        )
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12E34'])
            ).last_symbol,
            expression_module.Number(
                decimal.Decimal('12e34')
            )
        )
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12E+34'])
            ).last_symbol,
            expression_module.Number(
                decimal.Decimal('12e34')
            )
        )

    def test_parse_strip_zeros_fraction_part(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12.100e34'])
            ).last_symbol,
            expression_module.Number(
                decimal.Decimal('12.1e34')
            )
        )

    def test_parse_separators(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(["1'2'3'.1'0'0'e3'4'"])
            ).last_symbol,
            expression_module.Number(
                decimal.Decimal('123.1e34')
            )
        )

    def test_parse_normalize_trailing_zeros(self):
        number: expression_module.Number = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['123000'])
        ).last_symbol

        self.assertEqual(
            number,
            expression_module.Number(123000)
        )
        self.assertEqual(
            int,
            type(number.value)
        )


class StringTestCase(unittest.TestCase):
    def test_execute(self):
        # TODO: test local variable formatting
        self.assertEqual(
            'hello world',
            expression_module.String(
                is_binary=False,
                values=[
                    parser_module.String('hello '),
                    parser_module.String('world'),
                ],
            ).execute(namespace_module.Namespace())
        )
        self.assertEqual(
            b'hello world',
            expression_module.String(
                is_binary=True,
                values=[
                    parser_module.String(b'hello '),
                    parser_module.String(b'world'),
                ],
            ).execute(namespace_module.Namespace())
        )

    def test_string_text(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    '"foo"',
                    'f"""bar"""',
                ])
            ).last_symbol,
            expression_module.String(
                is_binary=False,
                values=[
                    parser_module.String('foo'),
                    parser_module.String('bar', is_formatted=True),
                ],
            )
        )

    def test_string_binary(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    'b"foo"',
                    'bf"""bar"""',
                ])
            ).last_symbol,
            expression_module.String(
                is_binary=True,
                values=[
                    parser_module.String(b'foo'),
                    parser_module.String(b'bar', is_formatted=True),
                ],
            )
        )

    def test_string_mixed_string_binary(self):
        with self.assertRaisesRegex(parser_module.ParseError,
                                    'all string literals must be binary, or none must be binary'):
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    '"foo"',
                    'bf"""bar"""',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError,
                                    'all string literals must be binary, or none must be binary'):
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    'b"foo"',
                    'f"""bar"""',
                ])
            )


class BooleanTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertIs(
            True,
            expression_module.Boolean(True).execute(namespace_module.Namespace())
        )
        self.assertIs(
            False,
            expression_module.Boolean(False).execute(namespace_module.Namespace())
        )

    def test_parse(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    ' True ',
                ])
            ).last_symbol,
            expression_module.Boolean(
                value=True,
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    ' False ',
                ])
            ).last_symbol,
            expression_module.Boolean(
                value=False,
            )
        )


class NoneValueTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertIs(
            None,
            expression_module.NoneValue().execute(namespace_module.Namespace())
        )

    def test_parse(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    ' None ',
                ])
            ).last_symbol,
            expression_module.NoneValue()
        )


class LValueTestCase(unittest.TestCase):
    def test_from_expression(self):
        # Already an LValue.
        self.assertEqual(
            expression_module.Variable('foo'),
            expression_module.LValue.from_expression(
                expression_module.Variable('foo')
            )
        )

        # Convert Parenthesized to Unpack.
        self.assertEqual(
            expression_module.Unpack([
                expression_module.Variable('foo')
            ]),
            expression_module.LValue.from_expression(
                expression_module.Parenthesized(
                    expression_module.Variable('foo')
                )
            )
        )

        # Convert Comma to Unpack.
        self.assertEqual(
            expression_module.Unpack([
                expression_module.Variable('foo'),
                expression_module.Variable('bar'),
            ]),
            expression_module.LValue.from_expression(
                expression_module.Comma(
                    expression_module.Variable('foo'),
                    expression_module.Variable('bar'),
                )
            )
        )

        # Combination of Parenthesized and Comma only becomes Unpack once.
        self.assertEqual(
            expression_module.Unpack([
                expression_module.Variable('foo'),
                expression_module.Variable('bar'),
            ]),
            expression_module.LValue.from_expression(
                expression_module.Parenthesized(
                    expression_module.Comma(
                        expression_module.Variable('foo'),
                        expression_module.Variable('bar'),
                    )
                )
            )
        )

        # Throw an exception if the Expression isn't an LValue.
        with self.assertRaisesRegex(parser_module.ParseError, 'expected LValue expression'):
            expression_module.LValue.from_expression(
                expression_module.Parenthesized(
                    expression_module.Comma(
                        expression_module.Variable('foo'),
                        expression_module.Call(),
                    )
                )
            )


class VariableTestCase(unittest.TestCase):
    def test_assign(self):
        namespace = namespace_module.Namespace()
        expression_module.Variable('foo').assign(namespace, 'foo value')

        self.assertEqual(
            'foo value',
            namespace.lookup('foo')
        )

    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('foo', 'foo value')
        namespace.declare('bar', 'bar value')

        self.assertEqual(
            'foo value',
            expression_module.Variable('foo').execute(namespace)
        )
        self.assertEqual(
            'bar value',
            expression_module.Variable('bar').execute(namespace)
        )

        with self.assertRaises(NameError):
            # This should eventually be a compile-time check, but for now
            # at least throw the same error as Python does.
            expression_module.Variable('baz').execute(namespace)

    def test_execute_initializer(self):
        namespace = namespace_module.Namespace()
        namespace.declare('foo', 'foo value')
        namespace.declare('bar', 'bar value')

        # "foo = bar"
        self.assertEqual(
            'bar value',
            expression_module.Variable(
                name='foo',
                initializer=expression_module.Variable('bar')
            ).execute(namespace)
        )
        self.assertEqual(
            'bar value',
            namespace.lookup('foo')
        )

        with self.assertRaises(NameError):
            # This should eventually be a compile-time check, but for now
            # at least throw the same error as Python does.
            expression_module.Variable('baz').execute(namespace)

    def test_parse(self):
        cursor = expression_module.Variable.parse(
            parser_module.Cursor(
                lines=['variable: annotation1, annotation2 = other_variable']
            ),
            parse_annotation=True,
            parse_initializer=True,
            allow_comma_in_annotations=True,
        )
        self.assertEqual(
            cursor,
            parser_module.Cursor(
                lines=['variable: annotation1, annotation2 = other_variable'],
                column=51,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotation=expression_module.Comma(
                        left=expression_module.Variable(
                            name='annotation1'
                        ),
                        right=expression_module.Variable(
                            name='annotation2'
                        ),
                    ),
                    initializer=expression_module.Variable(
                        name='other_variable',
                    ),
                ),
            )
        )

        # No spaces.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable:annotation1,annotation2=other_variable']
                ),
                parse_annotation=True,
                parse_initializer=True,
                allow_comma_in_annotations=True,
            ),
            parser_module.Cursor(
                lines=['variable:annotation1,annotation2=other_variable'],
                column=47,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotation=expression_module.Comma(
                        left=expression_module.Variable(
                            name='annotation1'
                        ),
                        right=expression_module.Variable(
                            name='annotation2'
                        ),
                    ),
                    initializer=expression_module.Variable(
                        name='other_variable',
                    ),
                ),
            )
        )

        # Trailing comma.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable: annotation1, annotation2, = other_variable']
                ),
                parse_annotation=True,
                parse_initializer=True,
                allow_comma_in_annotations=True,
            ),
            parser_module.Cursor(
                lines=['variable: annotation1, annotation2, = other_variable'],
                column=52,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotation=expression_module.Comma(
                        left=expression_module.Variable(
                            name='annotation1'
                        ),
                        right=expression_module.Variable(
                            name='annotation2'
                        ),
                    ),
                    initializer=expression_module.Variable(
                        name='other_variable',
                    ),
                ),
            )
        )

        # All spaces.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable  :  annotation1 , annotation2  =  other_variable']
                ),
                parse_annotation=True,
                parse_initializer=True,
                allow_comma_in_annotations=True,
            ),
            parser_module.Cursor(
                lines=['variable  :  annotation1 , annotation2  =  other_variable'],
                column=57,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotation=expression_module.Comma(
                        left=expression_module.Variable(
                            name='annotation1'
                        ),
                        right=expression_module.Variable(
                            name='annotation2'
                        ),
                    ),
                    initializer=expression_module.Variable(
                        name='other_variable',
                    ),
                ),
            )
        )

        # Annotations are optional.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable = other_variable']
                ),
                parse_annotation=True,
                parse_initializer=True,
                allow_comma_in_annotations=True,
            ),
            parser_module.Cursor(
                lines=['variable = other_variable'],
                column=25,
                last_symbol=expression_module.Variable(
                    name='variable',
                    initializer=expression_module.Variable(
                        name='other_variable',
                    ),
                ),
            )
        )

        # Initializers are optional.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable: annotation1, annotation2']
                ),
                parse_annotation=True,
                parse_initializer=True,
                allow_comma_in_annotations=True,
            ),
            parser_module.Cursor(
                lines=['variable: annotation1, annotation2'],
                column=34,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotation=expression_module.Comma(
                        left=expression_module.Variable(
                            name='annotation1'
                        ),
                        right=expression_module.Variable(
                            name='annotation2'
                        ),
                    ),
                ),
            )
        )

        # Initializers and annotations are optional.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable']
                ),
                parse_annotation=True,
                parse_initializer=True,
                allow_comma_in_annotations=True,
            ),
            parser_module.Cursor(
                lines=['variable'],
                column=8,
                last_symbol=expression_module.Variable(
                    name='variable',
                ),
            )
        )

    def test_parse_no_annotations(self):
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable = other_variable']
                ),
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable = other_variable'],
                column=25,
                last_symbol=expression_module.Variable(
                    name='variable',
                    initializer=expression_module.Variable(
                        name='other_variable',
                    ),
                ),
            )
        )

        # Unexpected annotations. Only parse the variable name, as the rest
        # of the line can be part of a larger expression.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable: annotation = other_variable']
                ),
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable: annotation = other_variable'],
                column=8,
                last_symbol=expression_module.Variable(
                    name='variable',
                ),
            )
        )

    def test_parse_no_initializer(self):
        # Unexpected initializer. Only parse the variable name, as the rest
        # of the line can be part of a larger expression.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable = other_variable']
                ),
            ),
            parser_module.Cursor(
                lines=['variable = other_variable'],
                column=8,
                last_symbol=expression_module.Variable(
                    name='variable',
                ),
            )
        )


class UnpackTestCase(unittest.TestCase):
    def test_assign(self):
        namespace = namespace_module.Namespace()

        expression_module.Unpack(lvalues=[
            expression_module.Variable('foo'),
            expression_module.Unpack(lvalues=[
                expression_module.Variable('bar'),
                expression_module.Variable('baz'),
            ])
        ]).assign(namespace, ['foo_value', ['bar_value', 'baz_value']])

        self.assertEqual(
            'foo_value',
            namespace.lookup('foo')
        )
        self.assertEqual(
            'bar_value',
            namespace.lookup('bar')
        )
        self.assertEqual(
            'baz_value',
            namespace.lookup('baz')
        )

        with self.assertRaisesRegex(ValueError, 'not enough values to unpack'):
            expression_module.Unpack([
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ]).assign(namespace, ['a'])

        with self.assertRaisesRegex(ValueError, 'too many values to unpack'):
            expression_module.Unpack([
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ]).assign(namespace, ['a', 'b', 'c'])

    def test_expressions(self):
        unpack = expression_module.Unpack([
            expression_module.Variable('a'),
            expression_module.Variable('b'),
        ])

        self.assertEqual(
            [
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ],
            list(unpack.expressions)
        )

    def test_variable_assignments(self):
        unpack = expression_module.Unpack([
            expression_module.Variable('a'),
            expression_module.Unpack([
                expression_module.Variable('b'),
                expression_module.Unpack([
                    expression_module.Variable('c'),
                    expression_module.Variable('d'),
                ]),
                expression_module.Variable('e'),
            ]),
            expression_module.Variable('f'),
        ])

        self.assertEqual(
            {
                expression_module.Variable('a'),
                expression_module.Variable('b'),
                expression_module.Variable('c'),
                expression_module.Variable('d'),
                expression_module.Variable('e'),
                expression_module.Variable('f'),
            },
            set(unpack.variable_assignments)
        )


class ParenthesizedTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertEqual(
            'value',
            expression_module.Parenthesized(
                expression_module.String.from_string('value')
            ).execute(namespace_module.Namespace())
        )

        # TODO: comma operator

    def test_expressions(self):
        my_parenthesized = expression_module.Parenthesized(
            expression=expression_module.Variable('foo'),
        )
        self.assertEqual(
            [
                expression_module.Variable('foo'),
            ],
            list(my_parenthesized.expressions)
        )

    def test_parse(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['(foo)'])
            ).last_symbol,
            expression_module.Parenthesized(
                expression=expression_module.Variable('foo')
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['(foo, bar)'])
            ).last_symbol,
            expression_module.Parenthesized(
                expression=expression_module.Comma(
                    left=expression_module.Variable('foo'),
                    right=expression_module.Variable('bar'),
                )
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['()'])
            ).last_symbol,
            expression_module.Parenthesized()
        )


class DictionaryOrSetTestCase(unittest.TestCase):
    def test_execute_set_one_item(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{1}'])
        ).last_symbol

        namespace = namespace_module.Namespace()

        self.assertEqual(
            {1},
            mapping.execute(namespace)
        )

    def test_execute_set_items(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{1, 2, 3}'])
        ).last_symbol

        namespace = namespace_module.Namespace()

        self.assertEqual(
            {1, 2, 3},
            mapping.execute(namespace)
        )

    def test_execute_set_star(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{*a}'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', {1, 2, 3})

        self.assertEqual(
            {1, 2, 3},
            mapping.execute(namespace)
        )

    def test_execute_set_star_comma(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{4, *a, 5}'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', {1, 2, 3})

        self.assertEqual(
            {1, 2, 3, 4, 5},
            mapping.execute(namespace)
        )

    def test_execute_dict_one_item(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{1: 2}'])
        ).last_symbol

        namespace = namespace_module.Namespace()

        self.assertEqual(
            {1: 2},
            mapping.execute(namespace)
        )

    def test_execute_dict_items(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{1: 2, 2: 3, 3: 4}'])
        ).last_symbol

        namespace = namespace_module.Namespace()

        self.assertEqual(
            {1: 2, 2: 3, 3: 4},
            mapping.execute(namespace)
        )

    def test_execute_dict_starstar(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{**a}'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', {1: 2, 2: 3, 3: 4})

        self.assertEqual(
            {1: 2, 2: 3, 3: 4},
            mapping.execute(namespace)
        )

    def test_execute_dict_starstar_comma(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{4: 5, **a, 5: 6}'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', {1: 2, 2: 3, 3: 4})

        self.assertEqual(
            {1: 2, 2: 3, 3: 4, 4: 5, 5: 6},
            mapping.execute(namespace)
        )

    def test_execute_set_comprehension(self):
        mapping: expression_module.List = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{i for i in range(4) if i != 2}'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('range', range)

        self.assertEqual(
            {0, 1, 3},  # skip 2
            mapping.execute(namespace)
        )

    def test_execute_dict_comprehension(self):
        mapping: expression_module.List = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{i: i*i for i in range(6) if i != 2}'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('range', range)

        self.assertEqual(
            {0: 0, 1: 1, 3: 9, 4: 16, 5: 25},  # skip 2
            mapping.execute(namespace)
        )

    def test_expressions(self):
        dict_or_set = expression_module.DictionaryOrSet(
            expression=expression_module.Variable('foo'),
        )
        self.assertEqual(
            [
                expression_module.Variable('foo'),
            ],
            list(dict_or_set.expressions)
        )

    def test_parse(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['{foo}'])
            ).last_symbol,
            expression_module.DictionaryOrSet(
                expression=expression_module.Variable('foo')
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['{foo, bar}'])
            ).last_symbol,
            expression_module.DictionaryOrSet(
                expression=expression_module.Comma(
                    left=expression_module.Variable('foo'),
                    right=expression_module.Variable('bar'),
                )
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['{}'])
            ).last_symbol,
            expression_module.DictionaryOrSet()
        )


class ListTestCase(unittest.TestCase):
    def test_execute_one_item(self):
        mapping: expression_module.List = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['[1]'])
        ).last_symbol

        namespace = namespace_module.Namespace()

        self.assertEqual(
            [1],
            mapping.execute(namespace)
        )

    def test_execute_items(self):
        mapping: expression_module.List = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['[1, 2, 3]'])
        ).last_symbol

        namespace = namespace_module.Namespace()

        self.assertEqual(
            [1, 2, 3],
            mapping.execute(namespace)
        )

    def test_execute_star(self):
        mapping: expression_module.List = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['[*a]'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', [1, 2, 3])

        self.assertEqual(
            [1, 2, 3],
            mapping.execute(namespace)
        )

    def test_execute_star_comma(self):
        mapping: expression_module.List = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['[4, *a, 5]'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', [1, 2, 3])

        self.assertEqual(
            [4, 1, 2, 3, 5],
            mapping.execute(namespace)
        )

    def test_execute_comprehension(self):
        mapping: expression_module.List = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['[i for i in range(4) if i != 2]'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('range', range)

        self.assertEqual(
            [0, 1, 3],
            mapping.execute(namespace)
        )

    def test_expressions(self):
        my_list = expression_module.List(
            expression=expression_module.Variable('foo'),
        )
        self.assertEqual(
            [
                expression_module.Variable('foo'),
            ],
            list(my_list.expressions)
        )

    def test_parse(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['[foo]'])
            ).last_symbol,
            expression_module.List(
                expression=expression_module.Variable('foo')
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['[foo, bar]'])
            ).last_symbol,
            expression_module.List(
                expression=expression_module.Comma(
                    left=expression_module.Variable('foo'),
                    right=expression_module.Variable('bar'),
                )
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['[]'])
            ).last_symbol,
            expression_module.List()
        )


class OperatorTestCase(unittest.TestCase):
    def test_operator_precedence(self):
        expected_precedence = (
            (expression_module.Call, expression_module.Dot, expression_module.Subscript),
            (expression_module.Exponentiation,),
            (expression_module.Positive, expression_module.Negative, expression_module.BitInverse),
            (expression_module.Multiply, expression_module.MatrixMultiply, expression_module.FloorDivide,
                expression_module.Divide, expression_module.Modulo),
            (expression_module.Add, expression_module.Subtract),
            (expression_module.ShiftLeft, expression_module.ShiftRight),
            (expression_module.BitAnd,),
            (expression_module.BitXor,),
            (expression_module.BitOr,),
            (expression_module.In, expression_module.NotIn, expression_module.IsNot, expression_module.Is,
                expression_module.LessThan, expression_module.LessThanOrEqual, expression_module.GreaterThan,
                expression_module.GreaterThanOrEqual, expression_module.NotEqual, expression_module.Equal),
            (expression_module.Not,),
            (expression_module.And,),
            (expression_module.Or,),
            (expression_module.IfElse,),
            (expression_module.Lambda,),
            (expression_module.Assignment,),
            (expression_module.Star, expression_module.StarStar),
            (expression_module.Colon,),
            (expression_module.Comprehension,),
            (expression_module.Comma,),
        )

        expected_higher_precedence_operators = set()
        for precedence_level in expected_precedence:
            for symbol_type in precedence_level:
                self.assertEqual(
                    expected_higher_precedence_operators,
                    symbol_type.higher_precedence_operators
                )

            expected_higher_precedence_operators.update(set(precedence_level))

    def test_precedes_on_right(self):
        # This behavior comes from the operator precedence rules, so just test a sample of cases.
        self.assertIs(
            True,
            expression_module.Call.precedes_on_right(expression_module.Not)
        )
        self.assertIs(
            False,
            expression_module.Not.precedes_on_right(expression_module.Call)
        )

        # Most operators should evaluate left to right.
        self.assertIs(
            False,
            expression_module.Not.precedes_on_right(expression_module.Not)
        )

        # ...with the exception of exponentiation...
        self.assertIs(
            True,
            expression_module.Exponentiation.precedes_on_right(expression_module.Exponentiation)
        )


class CallTestCase(unittest.TestCase):
    def test_execute(self):
        my_callable = mock.Mock(return_value='return value!')
        pos_1 = expression_module.String.from_string('pos_1')
        pos_2 = expression_module.String.from_string('pos_2')
        kwd_1 = expression_module.String.from_string('kwd_1')
        kwd_2 = expression_module.String.from_string('kwd_2')

        namespace = namespace_module.Namespace()
        namespace.declare('my_callable', my_callable)

        self.assertEqual(
            'return value!',
            expression_module.Call(
                callable=expression_module.Variable('my_callable'),
                positional_arguments=[pos_1, pos_2],
                keyword_arguments={
                    'keyword_1': kwd_1,
                    'keyword_2': kwd_2,
                },
            ).execute(namespace)
        )

        my_callable.assert_called_once_with(
            'pos_1',
            'pos_2',
            keyword_1='kwd_1',
            keyword_2='kwd_2',
        )

    def test_parse(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['a(b, c=d, e)'])
            ).last_symbol,
            expression_module.Call(
                callable=expression_module.Variable('a'),
                positional_arguments=[
                    expression_module.Variable('b'),
                    expression_module.Variable('e'),
                ],
                keyword_arguments={
                    'c': expression_module.Variable('d'),
                },
            )
        )

        # allow trailing comma
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['a(b, c=d, e,)'])
            ).last_symbol,
            expression_module.Call(
                callable=expression_module.Variable('a'),
                positional_arguments=[
                    expression_module.Variable('b'),
                    expression_module.Variable('e'),
                ],
                keyword_arguments={
                    'c': expression_module.Variable('d'),
                },
            )
        )

        # allow zero arguments
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['a()'])
            ).last_symbol,
            expression_module.Call(
                callable=expression_module.Variable('a'),
                positional_arguments=[],
                keyword_arguments={},
            )
        )

    def test_expressions(self):
        call = expression_module.Call(
            callable=expression_module.Variable('my_function'),
            positional_arguments=[
                expression_module.Variable('arg_1'),
                expression_module.Variable('arg_2'),
            ],
            keyword_arguments={
                'foo': expression_module.Variable('foo_arg'),
            },
        )

        self.assertEqual(
            [
                expression_module.Variable('my_function'),
                expression_module.Variable('arg_1'),
                expression_module.Variable('arg_2'),
                expression_module.Variable('foo_arg'),
            ],
            list(call.expressions)
        )


class DotTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        foo_value = mock.Mock(spec_set=['bar'])
        foo_value.bar = 'bar_value'
        namespace.declare('foo', foo_value)

        self.assertEqual(
            'bar_value',
            expression_module.Dot(
                object=expression_module.Variable('foo'),
                member_name='bar',
            ).execute(namespace)
        )

    def test_assign(self):
        namespace = namespace_module.Namespace()
        foo_value = mock.Mock(spec_set=['bar'])
        namespace.declare('foo', foo_value)

        expression_module.Dot(
            object=expression_module.Variable('foo'),
            member_name='bar',
        ).assign(namespace, 'bar_value')

        self.assertEqual(
            'bar_value',
            foo_value.bar
        )

    def test_expressions(self):
        dot = expression_module.Dot(
            object=expression_module.Variable('my_object'),
            member_name='foo',
        )

        self.assertEqual(
            [
                expression_module.Variable('my_object'),
            ],
            list(dot.expressions)
        )


class SubscriptTestCase(unittest.TestCase):
    def test_execute(self):
        subscriptable = mock.MagicMock()
        subscriptable.__getitem__.return_value = 'return value!'
        pos_1 = expression_module.String.from_string('pos_1')
        pos_2 = expression_module.String.from_string('pos_2')
        kwd_1 = expression_module.String.from_string('kwd_1')
        kwd_2 = expression_module.String.from_string('kwd_2')

        namespace = namespace_module.Namespace()
        namespace.declare('my_callable', subscriptable)

        self.assertEqual(
            'return value!',
            expression_module.Subscript(
                subscriptable=expression_module.Variable('my_callable'),
                positional_arguments=[pos_1, pos_2],
                keyword_arguments={
                    'keyword_1': kwd_1,
                    'keyword_2': kwd_2,
                },
            ).execute(namespace)
        )

        subscriptable.__getitem__.assert_called_once_with(
            'pos_1',
            'pos_2',
            keyword_1='kwd_1',
            keyword_2='kwd_2',
        )

    def test_assign(self):
        namespace = namespace_module.Namespace()
        foo_value = {}
        namespace.declare('foo', foo_value)

        expression_module.Subscript(
            subscriptable=expression_module.Variable('foo'),
            positional_arguments=[
                expression_module.String.from_string('bar')
            ],
        ).assign(namespace, 'bar_value')

        self.assertEqual(
            {
                'bar': 'bar_value'
            },
            foo_value
        )

    def test_parse(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['a[b, c=d, e]'])
            ).last_symbol,
            expression_module.Subscript(
                subscriptable=expression_module.Variable('a'),
                positional_arguments=[
                    expression_module.Variable('b'),
                    expression_module.Variable('e'),
                ],
                keyword_arguments={
                    'c': expression_module.Variable('d'),
                },
            )
        )

        # allow trailing comma
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['a[b, c=d, e,]'])
            ).last_symbol,
            expression_module.Subscript(
                subscriptable=expression_module.Variable('a'),
                positional_arguments=[
                    expression_module.Variable('b'),
                    expression_module.Variable('e'),
                ],
                keyword_arguments={
                    'c': expression_module.Variable('d'),
                },
            )
        )

        # allow zero arguments
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['a[]'])
            ).last_symbol,
            expression_module.Subscript(
                subscriptable=expression_module.Variable('a'),
                positional_arguments=[],
                keyword_arguments={},
            )
        )

    def test_expressions(self):
        subscript = expression_module.Subscript(
            subscriptable=expression_module.Variable('my_function'),
            positional_arguments=[
                expression_module.Variable('arg_1'),
                expression_module.Variable('arg_2'),
            ],
            keyword_arguments={
                'foo': expression_module.Variable('foo_arg'),
            },
        )

        self.assertEqual(
            [
                expression_module.Variable('my_function'),
                expression_module.Variable('arg_1'),
                expression_module.Variable('arg_2'),
                expression_module.Variable('foo_arg'),
            ],
            list(subscript.expressions)
        )


class ExponentiationTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertEqual(
            16,
            expression_module.Exponentiation(
                left=expression_module.Number(4),
                right=expression_module.Number(2),
            ).execute(namespace_module.Namespace())
        )


class PositiveTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertEqual(
            4,
            expression_module.Positive(
                expression_module.Number(4),
            ).execute(namespace_module.Namespace())
        )


class NegativeTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertEqual(
            -4,
            expression_module.Negative(
                expression_module.Number(4),
            ).execute(namespace_module.Namespace())
        )


class BitInverseTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('seven', 7)

        self.assertEqual(
            -8,
            expression_module.BitInverse(
                expression_module.Variable('seven'),
            ).execute(namespace)
        )


class MultiplyTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertEqual(
            8,
            expression_module.Multiply(
                left=expression_module.Number(4),
                right=expression_module.Number(2),
            ).execute(namespace_module.Namespace())
        )


class MatrixMultiplyTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()

        left = mock.MagicMock()
        left.__matmul__.return_value = 'result!'
        right = mock.MagicMock()

        namespace.declare('left', left)
        namespace.declare('right', right)

        self.assertEqual(
            'result!',
            expression_module.MatrixMultiply(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class FloorDivideTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 7)
        namespace.declare('right', 2)

        self.assertEqual(
            3,
            expression_module.FloorDivide(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class DivideTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 7)
        namespace.declare('right', 2)

        self.assertEqual(
            3.5,
            expression_module.Divide(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class ModuloTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 17)
        namespace.declare('right', 10)

        self.assertEqual(
            7,
            expression_module.Modulo(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class AddTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 17)
        namespace.declare('right', 10)

        self.assertEqual(
            27,
            expression_module.Add(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class SubtractTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 17)
        namespace.declare('right', 7)

        self.assertEqual(
            10,
            expression_module.Subtract(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class ShiftLeftTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 32)
        namespace.declare('right', 2)

        self.assertEqual(
            128,
            expression_module.ShiftLeft(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class ShiftRightTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 32)
        namespace.declare('right', 2)

        self.assertEqual(
            8,
            expression_module.ShiftRight(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class BitAndTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 7)  # 0111
        namespace.declare('right', 11)  # 1011

        self.assertEqual(
            3,  # 0011
            expression_module.BitAnd(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class BitXorTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 7)  # 0111
        namespace.declare('right', 11)  # 1011

        self.assertEqual(
            12,  # 1100
            expression_module.BitXor(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class BitOrTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('left', 5)  # 0101
        namespace.declare('right', 9)  # 1001

        self.assertEqual(
            13,  # 1101
            expression_module.BitOr(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class InTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', [1, 2, 3])

        namespace.declare('left', 2)
        self.assertIs(
            True,
            expression_module.In(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 6)
        self.assertIs(
            False,
            expression_module.In(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class NotInTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', [1, 2, 3])

        namespace.declare('left', 2)
        self.assertIs(
            False,
            expression_module.NotIn(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 6)
        self.assertIs(
            True,
            expression_module.NotIn(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class IsNotTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', False)

        namespace.declare('left', False)
        self.assertIs(
            False,
            expression_module.IsNot(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', True)
        self.assertIs(
            True,
            expression_module.IsNot(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class IsTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', False)

        namespace.declare('left', False)
        self.assertIs(
            True,
            expression_module.Is(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', True)
        self.assertIs(
            False,
            expression_module.Is(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class LessThanOrEqualTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', 10)

        namespace.declare('left', 9)
        self.assertIs(
            True,
            expression_module.LessThanOrEqual(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 10)
        self.assertIs(
            True,
            expression_module.LessThanOrEqual(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 11)
        self.assertIs(
            False,
            expression_module.LessThanOrEqual(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class LessThanTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', 10)

        namespace.declare('left', 9)
        self.assertIs(
            True,
            expression_module.LessThan(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 10)
        self.assertIs(
            False,
            expression_module.LessThan(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 11)
        self.assertIs(
            False,
            expression_module.LessThan(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class GreaterThanOrEqualTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', 10)

        namespace.declare('left', 9)
        self.assertIs(
            False,
            expression_module.GreaterThanOrEqual(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 10)
        self.assertIs(
            True,
            expression_module.GreaterThanOrEqual(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 11)
        self.assertIs(
            True,
            expression_module.GreaterThanOrEqual(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class GreaterThanTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', 10)

        namespace.declare('left', 9)
        self.assertIs(
            False,
            expression_module.GreaterThan(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 10)
        self.assertIs(
            False,
            expression_module.GreaterThan(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 11)
        self.assertIs(
            True,
            expression_module.GreaterThan(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class NotEqualTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', 10)

        namespace.declare('left', 9)
        self.assertIs(
            True,
            expression_module.NotEqual(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 10)
        self.assertIs(
            False,
            expression_module.NotEqual(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class EqualTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('right', 10)

        namespace.declare('left', 9)
        self.assertIs(
            False,
            expression_module.Equal(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', 10)
        self.assertIs(
            True,
            expression_module.Equal(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class NotTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('var', True)

        self.assertIs(
            False,
            expression_module.Not(
                expression=expression_module.Variable('var'),
            ).execute(namespace)
        )


class AndTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()

        namespace.declare('left', False)
        namespace.declare('right', False)
        self.assertIs(
            False,
            expression_module.And(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', False)
        namespace.declare('right', True)
        self.assertIs(
            False,
            expression_module.And(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', True)
        namespace.declare('right', True)
        self.assertIs(
            True,
            expression_module.And(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class OrTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()

        namespace.declare('left', False)
        namespace.declare('right', False)
        self.assertIs(
            False,
            expression_module.Or(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', False)
        namespace.declare('right', True)
        self.assertIs(
            True,
            expression_module.Or(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )

        namespace.declare('left', True)
        namespace.declare('right', True)
        self.assertIs(
            True,
            expression_module.Or(
                left=expression_module.Variable('left'),
                right=expression_module.Variable('right'),
            ).execute(namespace)
        )


class IfElseTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('true_value', 'true value')
        namespace.declare('false_value', 'false value')

        namespace.declare('condition', False)
        self.assertIs(
            'false value',
            expression_module.IfElse(
                condition=expression_module.Variable('condition'),
                true_value=expression_module.Variable('true_value'),
                false_value=expression_module.Variable('false_value'),
            ).execute(namespace)
        )

        namespace.declare('condition', True)
        self.assertIs(
            'true value',
            expression_module.IfElse(
                condition=expression_module.Variable('condition'),
                true_value=expression_module.Variable('true_value'),
                false_value=expression_module.Variable('false_value'),
            ).execute(namespace)
        )

    def test_expressions(self):
        if_else = expression_module.IfElse(
            condition=expression_module.Variable('condition'),
            true_value=expression_module.Variable('value'),
            false_value=expression_module.Variable('else_value'),
        )

        self.assertEqual(
            [
                expression_module.Variable('condition'),
                expression_module.Variable('value'),
                expression_module.Variable('else_value'),
            ],
            list(if_else.expressions)
        )


class LambdaTestCase(unittest.TestCase):
    def test_execute(self):
        add_one: expression_module.Lambda = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['(a, b = a + 1, c = my_global) -> [a, b, c]'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('my_global', 'My Global Value')

        self.assertEqual(
            [3, 4, 'My Global Value'],
            add_one.execute(namespace)(3)
        )

        self.assertEqual(
            [3, 'B', 'C'],
            add_one.execute(namespace)(3, 'B', c='C')
        )

    def test_parse_no_arguments(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['() -> foo'])
            ).last_symbol,
            expression_module.Lambda(
                arguments=argument_list.ArgumentList([]),
                expression=expression_module.Variable('foo'),
            )
        )

    def test_parse_arguments(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['(a, b) -> foo'])
            ).last_symbol,
            expression_module.Lambda(
                arguments=argument_list.ArgumentList([
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
                ]),
                expression=expression_module.Variable('foo'),
            )
        )

    def test_parse_argument_defaults(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['(a=b) -> foo'])
            ).last_symbol,
            expression_module.Lambda(
                arguments=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression_module.Variable(
                            'a',
                            initializer=expression_module.Variable('b')
                        ),
                        is_positional=True,
                        is_keyword=True,
                    ),
                ]),
                expression=expression_module.Variable('foo'),
            )
        )


class AssignmentTestCase(unittest.TestCase):
    def test_execute(self):
        assignment: expression_module.Assignment = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['(a := b)'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('b', 'B Value')

        self.assertEqual(
            'B Value',  # expression evaluates to right hand side value
            assignment.execute(namespace)
        )

        self.assertEqual(
            'B Value',  # and assignment took place
            namespace.lookup('a')
        )

    def test_expressions(self):
        assignment = expression_module.Assignment(
            left=expression_module.Variable('foo'),
            right=expression_module.Variable('bar'),
        )

        self.assertEqual(
            [
                expression_module.Variable('foo'),
                expression_module.Variable('bar'),
            ],
            list(assignment.expressions)
        )

    def test_variable_assignments(self):
        assignment = expression_module.Assignment(
            left=expression_module.Variable('foo'),
            right=expression_module.Variable('bar'),
        )

        self.assertEqual(
            [
                expression_module.Variable('foo')
            ],
            list(assignment.variable_assignments)
        )

        assignment = expression_module.Assignment(
            left=expression_module.Unpack([
                expression_module.Variable('foo'),
                expression_module.Variable('bar'),
            ]),
            right=expression_module.Variable('baz'),
        )

        self.assertEqual(
            [
                expression_module.Variable('foo'),
                expression_module.Variable('bar'),
            ],
            list(assignment.variable_assignments)
        )


class StarStarTestCase(unittest.TestCase):
    def test_execute_mapping(self):
        mapping: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{**a, **b}'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', {1: 2})
        namespace.declare('b', {3: 4})

        self.assertEqual(
            {1: 2, 3: 4},
            mapping.execute(namespace)
        )

    def test_execute_function_call(self):
        pass  # TODO: test function call argument expansion

    def test_execute_assignment(self):
        pass  # TODO: test assigning into a mapping


class StarTestCase(unittest.TestCase):
    def test_execute_list(self):
        my_list: expression_module.List = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['[*a, *b]'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', [1, 2])
        namespace.declare('b', [3, 4])

        self.assertEqual(
            [1, 2, 3, 4],
            my_list.execute(namespace)
        )

    def test_execute_set(self):
        my_list: expression_module.DictionaryOrSet = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['{*a, *b}'])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('a', [1, 2])
        namespace.declare('b', [3, 4])

        self.assertEqual(
            {1, 2, 3, 4},
            my_list.execute(namespace)
        )

    def test_execute_function_call(self):
        pass  # TODO: test function call argument expansion

    def test_execute_assignment(self):
        pass  # TODO: test assigning into a mapping


class ColonTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertEqual(
            expression_module.Colon.Pair(4, 2),
            expression_module.Colon(
                left=expression_module.Number(4),
                right=expression_module.Number(2),
            ).execute(namespace_module.Namespace())
        )


class ComprehensionTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()
        namespace.declare('iterable', range(6))

        comprehension: expression_module.Comprehension = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor(['i * i for i in iterable if i != 2'])
        ).last_symbol

        self.assertEqual(
            [0, 1, 9, 16, 25],  # exclude 2*2 = 4
            list(comprehension.execute(namespace))
        )

    def test_execute_multiple_loops(self):
        namespace = namespace_module.Namespace()
        namespace.declare('multiplier', range(4))
        namespace.declare('iterable', range(6))

        comprehension: expression_module.Comprehension = expression_module.ExpressionParser.parse(  # noqa
            parser_module.Cursor([
                'outer * inner',
                'for outer in multiplier',
                'for inner in iterable',
                'if outer != inner',
            ])
        ).last_symbol

        self.assertEqual(
            [
                0, 0, 0, 0, 0,  # multiplier == 0, skip 0*0 = 0
                0, 2, 3, 4, 5,  # multiplier == 1, skip 1*1 = 1
                0, 2, 6, 8, 10,  # multiplier == 2, skip 2*2 = 4
                0, 3, 6, 12, 15,  # multiplier == 3, skip 3*3 = 9
            ],
            list(comprehension.execute(namespace))
        )

    def test_expressions(self):
        comprehension = expression_module.Comprehension(
            value=expression_module.Variable('value'),
            loops=[],
        )

        self.assertEqual(
            [
                expression_module.Variable('value'),
            ],
            list(comprehension.expressions)
        )

        comprehension = expression_module.Comprehension(
            value=expression_module.Variable('value'),
            loops=[
                expression_module.Comprehension.Loop(
                    iterable=expression_module.Variable('iterable'),
                    receiver=expression_module.Variable('receiver'),
                ),
            ],
            condition=expression_module.Variable('condition'),
        )

        self.assertEqual(
            [
                expression_module.Variable('iterable'),
                expression_module.Variable('receiver'),
                expression_module.Variable('value'),
                expression_module.Variable('condition'),
            ],
            list(comprehension.expressions)
        )

    def test_parse(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['a for b in c'])
            ).last_symbol,
            expression_module.Comprehension(
                value=expression_module.Variable('a'),
                loops=[
                    expression_module.Comprehension.Loop(
                        receiver=expression_module.Variable('b'),
                        iterable=expression_module.Variable('c'),
                    )
                ],
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    'a for b in c',
                    'for d in e',
                ])
            ).last_symbol,
            expression_module.Comprehension(
                value=expression_module.Variable('a'),
                loops=[
                    expression_module.Comprehension.Loop(
                        receiver=expression_module.Variable('b'),
                        iterable=expression_module.Variable('c'),
                    ),
                    expression_module.Comprehension.Loop(
                        receiver=expression_module.Variable('d'),
                        iterable=expression_module.Variable('e'),
                    ),
                ],
            )
        )

        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor([
                    'a for b in c',
                    'for d in e',
                    'if f',
                ])
            ).last_symbol,
            expression_module.Comprehension(
                value=expression_module.Variable('a'),
                loops=[
                    expression_module.Comprehension.Loop(
                        receiver=expression_module.Variable('b'),
                        iterable=expression_module.Variable('c'),
                    ),
                    expression_module.Comprehension.Loop(
                        receiver=expression_module.Variable('d'),
                        iterable=expression_module.Variable('e'),
                    ),
                ],
                condition=expression_module.Variable('f'),
            )
        )


class CommaTestCase(unittest.TestCase):
    def test_expressions(self):
        comma = expression_module.Comma(
            left=expression_module.Variable('foo'),
            right=expression_module.Variable('bar'),
        )

        self.assertEqual(
            [
                expression_module.Variable('foo'),
                expression_module.Variable('bar'),
            ],
            list(comma.expressions)
        )

    def test_to_expression_list(self):
        self.assertEqual(
            [
                expression_module.Variable('a'),
                expression_module.Variable('b'),
                expression_module.Variable('c'),
                expression_module.Variable('d'),
            ],
            list(expression_module.Comma(
                left=expression_module.Comma(
                    left=expression_module.Variable('a'),
                    right=expression_module.Variable('b'),
                ),
                right=expression_module.Comma(
                    left=expression_module.Variable('c'),
                    right=expression_module.Variable('d'),
                ),
            ).to_expression_list())
        )


class ExpressionParserTestCase(unittest.TestCase):
    @staticmethod
    def parse_expression(expression_text, **kwds):
        return expression_module.ExpressionParser.parse(
            cursor=parser_module.Cursor(expression_text.splitlines()),
            **kwds
        ).last_symbol

    def test_parse_prefix_operators(self):
        self.assertEqual(
            expression_module.Positive(
                expression_module.Variable('foo')
            ),
            self.parse_expression('+foo')
        )
        self.assertEqual(
            expression_module.Negative(
                expression_module.Variable('foo')
            ),
            self.parse_expression('-foo')
        )
        self.assertEqual(
            expression_module.BitInverse(
                expression_module.Variable('foo')
            ),
            self.parse_expression('~foo')
        )
        self.assertEqual(
            expression_module.Not(
                expression_module.Variable('foo')
            ),
            self.parse_expression('not foo')
        )
        self.assertEqual(
            expression_module.Lambda(
                expression=expression_module.Variable('foo'),
            ),
            self.parse_expression('() -> foo')
        )
        self.assertEqual(
            expression_module.StarStar(
                expression_module.Variable('foo')
            ),
            self.parse_expression('**foo')
        )
        self.assertEqual(
            expression_module.Star(
                expression_module.Variable('foo')
            ),
            self.parse_expression('*foo')
        )

    def test_parse_infix_operators(self):
        self.assertEqual(
            expression_module.Exponentiation(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a ** b')
        )
        self.assertEqual(
            expression_module.Multiply(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a * b')
        )
        self.assertEqual(
            expression_module.MatrixMultiply(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a @ b')
        )
        self.assertEqual(
            expression_module.Divide(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a / b')
        )
        self.assertEqual(
            expression_module.FloorDivide(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a // b')
        )
        self.assertEqual(
            expression_module.Modulo(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a % b')
        )
        self.assertEqual(
            expression_module.Add(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a + b')
        )
        self.assertEqual(
            expression_module.Subtract(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a - b')
        )
        self.assertEqual(
            expression_module.ShiftLeft(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a << b')
        )
        self.assertEqual(
            expression_module.ShiftRight(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a >> b')
        )
        self.assertEqual(
            expression_module.BitAnd(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a & b')
        )
        self.assertEqual(
            expression_module.BitXor(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a ^ b')
        )
        self.assertEqual(
            expression_module.BitOr(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a | b')
        )
        self.assertEqual(
            expression_module.In(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a in b')
        )
        self.assertEqual(
            expression_module.NotIn(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a not in b')
        )
        self.assertEqual(
            expression_module.Is(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a is b')
        )
        self.assertEqual(
            expression_module.IsNot(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a is not b')
        )
        self.assertEqual(
            expression_module.LessThan(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a < b')
        )
        self.assertEqual(
            expression_module.LessThanOrEqual(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a <= b')
        )
        self.assertEqual(
            expression_module.GreaterThan(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a > b')
        )
        self.assertEqual(
            expression_module.GreaterThanOrEqual(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a >= b')
        )
        self.assertEqual(
            expression_module.NotEqual(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a != b')
        )
        self.assertEqual(
            expression_module.Equal(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a == b')
        )
        self.assertEqual(
            expression_module.And(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a and b')
        )
        self.assertEqual(
            expression_module.Or(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a or b')
        )
        self.assertEqual(
            expression_module.IfElse(
                condition=expression_module.Variable('condition'),
                true_value=expression_module.Variable('true_value'),
                false_value=expression_module.Variable('false_value'),
            ),
            self.parse_expression('true_value if condition else false_value')
        )
        self.assertEqual(
            expression_module.Assignment(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a := b')
        )
        self.assertEqual(
            expression_module.Colon(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a : b')
        )
        self.assertEqual(
            expression_module.Comma(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a, b')
        )

    def test_parse_immediate_operators(self):
        self.assertEqual(
            expression_module.Call(
                callable=expression_module.Variable('callable'),
                positional_arguments=[
                    expression_module.Variable('arg_1'),
                    expression_module.Variable('arg_2'),
                ],
                keyword_arguments={
                    'kwarg': expression_module.Variable('foo'),
                },
            ),
            self.parse_expression('callable(arg_1, arg_2, kwarg=foo)')
        )
        self.assertEqual(
            expression_module.Dot(
                object=expression_module.Variable('foo'),
                member_name='bar',
            ),
            self.parse_expression('foo.bar')
        )
        self.assertEqual(
            expression_module.Subscript(
                subscriptable=expression_module.Variable('subscriptable'),
                positional_arguments=[
                    expression_module.Variable('arg_1'),
                    expression_module.Variable('arg_2'),
                ],
                keyword_arguments={
                    'kwarg': expression_module.Variable('foo'),
                },
            ),
            self.parse_expression('subscriptable[arg_1, arg_2, kwarg=foo]')
        )

    def test_precedence_prefix(self):
        # Prefix operators should be evaluated right to left.
        self.assertEqual(
            expression_module.Negative(
                expression_module.Not(
                    expression_module.Variable('a')
                )
            ),
            self.parse_expression('-not a')
        )
        self.assertEqual(
            expression_module.Not(
                expression_module.Negative(
                    expression_module.Variable('a')
                )
            ),
            self.parse_expression('not -a')
        )

    def test_precedence_infix_equal_precedence(self):
        self.assertEqual(
            expression_module.Add(
                expression_module.Add(
                    expression_module.Variable('a'),
                    expression_module.Variable('b'),
                ),
                expression_module.Variable('c'),
            ),
            self.parse_expression('a + b + c')
        )
        self.assertEqual(
            expression_module.Multiply(
                expression_module.Multiply(
                    expression_module.Variable('a'),
                    expression_module.Variable('b'),
                ),
                expression_module.Variable('c'),
            ),
            self.parse_expression('a * b * c')
        )

    def test_precedence_infix_unequal_precedence(self):
        self.assertEqual(
            expression_module.Add(
                expression_module.Variable('a'),
                expression_module.Multiply(
                    expression_module.Variable('b'),
                    expression_module.Variable('c'),
                ),
            ),
            self.parse_expression('a + b * c')
        )
        self.assertEqual(
            expression_module.Add(
                expression_module.Multiply(
                    expression_module.Variable('a'),
                    expression_module.Variable('b'),
                ),
                expression_module.Variable('c'),
            ),
            self.parse_expression('a * b + c')
        )

    def test_precedence_infix_right_to_left(self):
        # The exponentiation operator evaluates right to left.
        self.assertEqual(
            expression_module.Exponentiation(
                expression_module.Variable('a'),
                expression_module.Exponentiation(
                    expression_module.Variable('b'),
                    expression_module.Variable('c'),
                ),
            ),
            self.parse_expression('a ** b ** c')
        )

        # If the right-most operator is lower precedence, evaluate
        # left to right.
        self.assertEqual(
            expression_module.Multiply(
                expression_module.Exponentiation(
                    expression_module.Variable('a'),
                    expression_module.Variable('b'),
                ),
                expression_module.Variable('c'),
            ),
            self.parse_expression('a ** b * c')
        )

    def test_precedence_infix_prefix(self):
        # The infix operator is higher precedence.
        self.assertEqual(
            expression_module.Negative(
                expression_module.Exponentiation(
                    expression_module.Variable('a'),
                    expression_module.Variable('b'),
                )
            ),
            self.parse_expression('-a**b')
        )

        # The prefix operator wins when placed before the second operand.
        self.assertEqual(
            expression_module.Exponentiation(
                expression_module.Variable('a'),
                expression_module.Negative(
                    expression_module.Variable('b'),
                )
            ),
            self.parse_expression('a ** -b')
        )
        self.assertEqual(
            expression_module.Subtract(
                expression_module.Variable('a'),
                expression_module.Negative(
                    expression_module.Variable('b'),
                )
            ),
            self.parse_expression('a - -b')
        )

        # The infix operator is lower precedence.
        self.assertEqual(
            expression_module.Multiply(
                expression_module.Negative(
                    expression_module.Variable('a')
                ),
                expression_module.Variable('b'),
            ),
            self.parse_expression('-a * b')
        )
        self.assertEqual(
            expression_module.Multiply(
                expression_module.Variable('a'),
                expression_module.Negative(
                    expression_module.Variable('b')
                ),
            ),
            self.parse_expression('a * -b')
        )

    def test_precedence_immediate(self):
        # Immediate operators are evaluated left to right.
        self.assertEqual(
            expression_module.Dot(
                object=expression_module.Subscript(
                    subscriptable=expression_module.Call(
                        callable=expression_module.Variable('a'),
                        positional_arguments=[expression_module.Variable('b')],
                    ),
                    positional_arguments=[expression_module.Variable('c')],
                ),
                member_name='foo',
            ),
            self.parse_expression('a(b)[c].foo')
        )

        # Or inner-most to outer-most.
        self.assertEqual(
            expression_module.Call(
                callable=expression_module.Variable('a'),
                positional_arguments=[expression_module.Subscript(
                    subscriptable=expression_module.Variable('b'),
                    positional_arguments=[expression_module.Dot(
                        object=expression_module.Variable('c'),
                        member_name='foo',
                    )],
                )],
            ),
            self.parse_expression('a(b[c.foo])')
        )

    def test_precedence_immediate_prefix(self):
        self.assertEqual(
            expression_module.BitInverse(
                expression_module.Dot(
                    expression_module.Variable('a'),
                    member_name='foo',
                )
            ),
            self.parse_expression('~a.foo')
        )

    def test_precedence_immediate_infix(self):
        self.assertEqual(
            expression_module.Add(
                expression_module.Dot(
                    expression_module.Variable('a'),
                    member_name='foo',
                ),
                expression_module.Dot(
                    expression_module.Variable('b'),
                    member_name='bar',
                ),
            ),
            self.parse_expression('a.foo + b.bar')
        )

    def test_allow_newline(self):
        # Allow newlines by default.
        self.assertEqual(
            expression_module.Add(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('\n'.join([
                'a',
                '+',
                'b',
            ]))
        )

        # Stop the expression on the first newline EndLine in stop_symbols.
        self.assertEqual(
            expression_module.Variable('a'),
            self.parse_expression('\n'.join([
                'a',
                '+',
                'b',
            ]), stop_symbols=[parser_module.EndLine])
        )

        # However, if we've just consumed a prefix operator, continue to parse.
        self.assertEqual(
            expression_module.Negative(
                expression_module.Variable('a')
            ),
            self.parse_expression('\n'.join([
                '-',
                'a',  # stop parsing here
                'b',  # ignore
            ]), stop_symbols=[parser_module.EndLine])
        )

        # Same with an infix operator.
        self.assertEqual(
            expression_module.Add(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('\n'.join([
                'a +',
                'b',
            ]), stop_symbols=[parser_module.EndLine])
        )

    def test_allow_colon(self):
        # By default, allow colon.
        self.assertEqual(
            expression_module.Colon(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a:b')
        )

        # Stop parsing at ":" if ":" in stop_symbols.
        self.assertEqual(
            expression_module.Variable('a'),
            self.parse_expression('a:b', stop_symbols=[parser_module.Characters[':']])
        )

    def test_allow_comma(self):
        # By default, allow comma.
        self.assertEqual(
            expression_module.Comma(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a, b')
        )

        # Stop parsing at "," if "," in stop_symbols.
        self.assertEqual(
            expression_module.Variable('a'),
            self.parse_expression('a, b', stop_symbols=[parser_module.Characters[',']])
        )

    def test_ignore_trailing_comma(self):
        self.assertEqual(
            expression_module.Comma(
                expression_module.Variable('a'),
                expression_module.Variable('b'),
            ),
            self.parse_expression('a, b,')
        )

        self.assertEqual(
            expression_module.Variable('a'),
            self.parse_expression('a,')
        )

    def test_expected_an_operand(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected an operand'):
            self.parse_expression('a + +')

        with self.assertRaisesRegex(parser_module.ParseError, 'expected an operand'):
            self.parse_expression('a +')
