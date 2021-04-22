import decimal
import unittest

from . import expression as expression_module, argument_list, namespace as namespace_module
from ..libs import parser as parser_module

# pylint: disable=fixme
# pylint: disable=too-many-lines


class NumberTestCase(unittest.TestCase):
    def test_execute(self):
        self.assertEqual(
            decimal.Decimal('-12.34e-56'),
            expression_module.Number(
                digits_part=-1234,
                magnitude_part=-58,
            ).execute(namespace_module.Namespace())
        )

    def test_parse_float(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12.34e-56'])
            ).last_symbol,
            expression_module.Number(
                digits_part=1234,
                magnitude_part=-58,
            )
        )

    def test_parse_integer(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['1234'])
            ).last_symbol,
            expression_module.Number(
                digits_part=1234,
                magnitude_part=0,
            )
        )

    def test_parse_float_no_magnitude(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12.34'])
            ).last_symbol,
            expression_module.Number(
                digits_part=1234,
                magnitude_part=-2,
            )
        )

    def test_parse_integer_magnitude(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12e34'])
            ).last_symbol,
            expression_module.Number(
                digits_part=12,
                magnitude_part=34,
            )
        )
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12E34'])
            ).last_symbol,
            expression_module.Number(
                digits_part=12,
                magnitude_part=34,
            )
        )
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12E+34'])
            ).last_symbol,
            expression_module.Number(
                digits_part=12,
                magnitude_part=34,
            )
        )

    def test_parse_strip_zeros_fraction_part(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['12.100e34'])
            ).last_symbol,
            expression_module.Number(
                digits_part=121,
                magnitude_part=33,
            )
        )

    def test_parse_separators(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(["1'2'3'.1'0'0'e3'4'"])
            ).last_symbol,
            expression_module.Number(
                digits_part=1231,
                magnitude_part=33,
            )
        )

    def test_parse_normalize_trailing_zeros(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['123000'])
            ).last_symbol,
            expression_module.Number(
                digits_part=123,
                magnitude_part=3,
            )
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
    def test_expressions(self):
        pass


class PositiveTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class NegativeTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class BitInverseTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class MultiplyTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class MatrixMultiplyTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class FloorDivideTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class DivideTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class ModuloTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class AddTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class SubtractTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class ShiftLeftTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class ShiftRightTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class BitAndTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class BitXorTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class BitOrTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class InTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class NotInTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class IsNotTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class IsTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class LessThanOrEqualTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class LessThanTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class GreaterThanOrEqualTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class GreaterThanTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class NotEqualTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class EqualTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class NotTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class AndTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class OrTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class IfElseTestCase(unittest.TestCase):
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
    def test_expressions(self):
        pass

    def test_parse_no_arguments(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['lambda: foo'])
            ).last_symbol,
            expression_module.Lambda(
                arguments=argument_list.ArgumentList([]),
                expression=expression_module.Variable('foo'),
            )
        )

    def test_parse_arguments(self):
        self.assertEqual(
            expression_module.ExpressionParser.parse(
                parser_module.Cursor(['lambda a, b: foo'])
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
                parser_module.Cursor(['lambda a=b: foo'])
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
    def test_expressions(self):
        pass


class StarTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class ColonTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class ComprehensionTestCase(unittest.TestCase):
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
            self.parse_expression('lambda: foo')
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
