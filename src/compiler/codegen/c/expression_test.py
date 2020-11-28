import unittest

from . import expression
from .types import integer


class ExpressionTestCase(unittest.TestCase):
    def test_integer_literal_expression(self):
        expectations = {
            expression.IntegerLiteral(value=42, width=16, signed=True): '42',
            expression.IntegerLiteral(value=-42, width=16, signed=True): '-42',
            expression.IntegerLiteral(value=42, width=32, signed=True): '42l',
            expression.IntegerLiteral(value=-42, width=32, signed=True): '-42l',
            expression.IntegerLiteral(value=42, width=64, signed=True): '42ll',
            expression.IntegerLiteral(value=-42, width=64, signed=True): '-42ll',
            expression.IntegerLiteral(value=42, width=16, signed=False): '42u',
            expression.IntegerLiteral(value=42, width=32, signed=False): '42ul',
            expression.IntegerLiteral(value=42, width=64, signed=False): '42ull',
        }

        for expr, expected_output in expectations.items():
            self.assertEqual(
                [expected_output],
                list(expr.render_expression())
            )

    def test_integer_literal_expression_default_width(self):
        self.assertEqual(16, expression.IntegerLiteral(0).width)

        self.assertEqual(16, expression.IntegerLiteral(-32768).width)
        self.assertEqual(32, expression.IntegerLiteral(-32769).width)
        self.assertEqual(16, expression.IntegerLiteral(32767).width)
        self.assertEqual(32, expression.IntegerLiteral(32768).width)

        self.assertEqual(32, expression.IntegerLiteral(-2147483648).width)
        self.assertEqual(64, expression.IntegerLiteral(-2147483649).width)
        self.assertEqual(32, expression.IntegerLiteral(2147483647).width)
        self.assertEqual(64, expression.IntegerLiteral(2147483648).width)

        self.assertEqual(64, expression.IntegerLiteral(18446744073709551615).width)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(18446744073709551616)

        self.assertEqual(
            'value 18446744073709551616 out of range (signed=False, width=64)',
            str(cm.exception)
        )

    def test_integer_literal_expression_default_signed(self):
        # If a number is too wide for a signed integer, use unsigned.
        self.assertEqual(True, expression.IntegerLiteral(0, width=16).signed)
        self.assertEqual(True, expression.IntegerLiteral(-1, width=16).signed)
        self.assertEqual(True, expression.IntegerLiteral(32767, width=16).signed)
        self.assertEqual(False, expression.IntegerLiteral(32768, width=16).signed)

        self.assertEqual(True, expression.IntegerLiteral(0, width=32).signed)
        self.assertEqual(True, expression.IntegerLiteral(-1, width=32).signed)
        self.assertEqual(True, expression.IntegerLiteral(2147483647, width=32).signed)
        self.assertEqual(False, expression.IntegerLiteral(2147483648, width=32).signed)

        self.assertEqual(True, expression.IntegerLiteral(0, width=64).signed)
        self.assertEqual(True, expression.IntegerLiteral(-1, width=64).signed)
        self.assertEqual(True, expression.IntegerLiteral(9223372036854775807, width=64).signed)
        self.assertEqual(False, expression.IntegerLiteral(9223372036854775808, width=64).signed)

    def test_integer_literal_range_validator_16(self):
        expression.IntegerLiteral(32767, width=16, signed=True)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(32768, width=16, signed=True)

        self.assertEqual(
            'value 32768 out of range (signed=True, width=16)',
            str(cm.exception)
        )

        expression.IntegerLiteral(-32768, width=16, signed=True)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(-32769, width=16, signed=True)

        self.assertEqual(
            'value -32769 out of range (signed=True, width=16)',
            str(cm.exception)
        )

        expression.IntegerLiteral(65535, width=16, signed=False)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(65536, width=16, signed=False)

        self.assertEqual(
            'value 65536 out of range (signed=False, width=16)',
            str(cm.exception)
        )

        expression.IntegerLiteral(0, width=16, signed=False)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(-1, width=16, signed=False)

        self.assertEqual(
            'value -1 out of range (signed=False, width=16)',
            str(cm.exception)
        )

    def test_integer_literal_range_validator_32(self):
        expression.IntegerLiteral(2147483647, width=32, signed=True)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(2147483648, width=32, signed=True)

        self.assertEqual(
            'value 2147483648 out of range (signed=True, width=32)',
            str(cm.exception)
        )

        expression.IntegerLiteral(-2147483648, width=32, signed=True)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(-2147483649, width=32, signed=True)

        self.assertEqual(
            'value -2147483649 out of range (signed=True, width=32)',
            str(cm.exception)
        )

        expression.IntegerLiteral(4294967295, width=32, signed=False)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(4294967296, width=32, signed=False)

        self.assertEqual(
            'value 4294967296 out of range (signed=False, width=32)',
            str(cm.exception)
        )

        expression.IntegerLiteral(0, width=32, signed=False)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(-1, width=32, signed=False)

        self.assertEqual(
            'value -1 out of range (signed=False, width=32)',
            str(cm.exception)
        )

    def test_integer_literal_range_validator_64(self):
        expression.IntegerLiteral(9223372036854775807, width=64, signed=True)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(9223372036854775808, width=64, signed=True)

        self.assertEqual(
            'value 9223372036854775808 out of range (signed=True, width=64)',
            str(cm.exception)
        )

        expression.IntegerLiteral(-9223372036854775808, width=64, signed=True)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(-9223372036854775809, width=64, signed=True)

        self.assertEqual(
            'value -9223372036854775809 out of range (signed=True, width=64)',
            str(cm.exception)
        )

        expression.IntegerLiteral(18446744073709551615, width=64, signed=False)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(18446744073709551616, width=64, signed=False)

        self.assertEqual(
            'value 18446744073709551616 out of range (signed=False, width=64)',
            str(cm.exception)
        )

        expression.IntegerLiteral(0, width=64, signed=False)

        with self.assertRaises(ValueError) as cm:
            expression.IntegerLiteral(-1, width=64, signed=False)

        self.assertEqual(
            'value -1 out of range (signed=False, width=64)',
            str(cm.exception)
        )

    def test_bytes_literal_expression(self):
        self.assertEqual(
            ['""'],
            list(expression.BytesLiteral(b'').render_expression())
        )
        self.assertEqual(
            ['"hello world"'],
            list(expression.BytesLiteral(b'hello world').render_expression())
        )
        self.assertEqual(
            ['"Don\\\'t Panic!\\000"'],
            list(expression.BytesLiteral(b'Don\'t Panic!\0').render_expression())
        )
        self.assertEqual(
            [
                '"line one "',
                ('  ', '"line two"')
            ],
            list(expression.BytesLiteral(b'line one line two', chunk_size=9).render_expression())
        )

    def test_variable(self):
        self.assertEqual(
            ['foo'],
            list(expression.Variable(name='foo').render_expression())
        )

    def test_dot(self):
        self.assertEqual(
            [
                ('foo', '.', 'bar')
            ],
            list(expression.Dot(
                expression.Variable(name='foo'),
                member='bar',
            ).render_expression())
        )

        self.assertEqual(
            [
                '"hello "',
                (('  ', '"world!"'), '.', 'bar')
            ],
            list(expression.Dot(
                expression.BytesLiteral(b'hello world!', 6),
                member='bar',
            ).render_expression())
        )

    def test_arrow(self):
        self.assertEqual(
            [
                ('foo', '->', 'bar')
            ],
            list(expression.Arrow(
                expression.Variable(name='foo'),
                member='bar',
            ).render_expression())
        )

        self.assertEqual(
            [
                '"hello "',
                (('  ', '"world!"'), '->', 'bar')
            ],
            list(expression.Arrow(
                expression.BytesLiteral(b'hello world!', 6),
                member='bar',
            ).render_expression())
        )

    def test_call(self):
        self.assertEqual(
            [
                ('foo', '('),
                ('  ', 'bar'),
                (')'),
            ],
            list(expression.Call(
                expression.Variable(name='foo'),
                [expression.Variable(name='bar')],
            ).render_expression())
        )

        self.assertEqual(
            [
                '"hello "',
                (('  ', '"world!"'), '('),
                ('  ', '"foo "'),
                ('  ', ('  ', '"bar "')),
                ('  ', ('  ', '"baz"')),
                ')',
            ],
            list(expression.Call(
                expression.BytesLiteral(b'hello world!', 6),
                [expression.BytesLiteral(b'foo bar baz', 4)],
            ).render_expression())
        )

        self.assertEqual(
            [
                '"hello "',
                (('  ', '"world!"'), '('),
                ('  ', '"foo "'),
                ('  ', ('  ', '"bar"'), ','),
                ('  ', '"baz"'),
                ')',
            ],
            list(expression.Call(
                expression.BytesLiteral(b'hello world!', 6),
                [
                    expression.BytesLiteral(b'foo bar', 4),
                    expression.BytesLiteral(b'baz', 4),
                ],
            ).render_expression())
        )

    def test_subscript(self):
        self.assertEqual(
            [
                ('foo', '[', 'bar', ']')
            ],
            list(expression.Subscript(
                expression.Variable(name='foo'),
                expression.Variable(name='bar'),
            ).render_expression())
        )

        self.assertEqual(
            [
                '"hello "',
                (('  ', '"world!"'), '[', '"foo "'),
                ('  ', '"bar "'),
                (('  ', '"baz"'), ']')
            ],
            list(expression.Subscript(
                expression.BytesLiteral(b'hello world!', 6),
                expression.BytesLiteral(b'foo bar baz', 4),
            ).render_expression())
        )

    def test_unary_operators(self):
        all_unary_operators = [
            cls for cls in vars(expression).values()
            if isinstance(cls, type) and issubclass(cls, expression.UnaryOperatorExpression)
            and cls is not expression.UnaryOperatorExpression
            and cls is not expression.Cast
        ]

        expected_operators = {
            expression.Increment: '++',
            expression.Decrement: '--',
            expression.AddressOf: '&',
            expression.Dereference: '*',
            expression.Positive: '+',
            expression.Negative: '-',
            expression.BitwiseNot: '~',
            expression.Not: '!',
            expression.SizeOf: 'sizeof ',
        }

        self.assertSetEqual(set(expected_operators.keys()), set(all_unary_operators))

        for cls, expected_operator in expected_operators.items():
            # noinspection PyArgumentList
            self.assertEqual(
                [
                    ('(', expected_operator, 'foo', ')'),
                ],
                list(cls(
                    expression.Variable(name='foo'),
                ).render_expression())
            )

            # noinspection PyArgumentList
            self.assertEqual(
                [
                    ('(', expected_operator, '"hello "'),
                    ('  ', '"there "'),
                    (('  ', '"world!"'), ')'),
                ],
                list(cls(
                    expression.BytesLiteral(b'hello there world!', 6),
                ).render_expression())
            )

    def test_unary_operators(self):
        self.assertEqual(
            [
                ('(', '(int)', 'foo', ')'),
            ],
            list(expression.Cast(
                expression.Variable(name='foo'),
                integer.Int(),
            ).render_expression())
        )

        self.assertEqual(
            [
                ('(', '(int)', '"hello "'),
                ('  ', '"there "'),
                (('  ', '"world!"'), ')'),
            ],
            list(expression.Cast(
                expression.BytesLiteral(b'hello there world!', 6),
                integer.Int(),
            ).render_expression())
        )

    def test_assign(self):
        self.assertEqual(
            [
                ('(', 'foo'),
                ('  ', '=', ' ', '42', ')'),
            ],
            list(expression.Assign(
                left=expression.Variable(name='foo'),
                right=expression.IntegerLiteral(42),
            ).render_expression())
        )

        class MultilineLValue(expression.LValueExpression):
            def render_expression(self):
                yield 'line_1'
                yield '  ', 'line_2'

        self.assertEqual(
            [
                ('(', 'line_1'),
                ('  ', 'line_2'),
                ('  ', '=', ' ', '"hello "'),
                ('  ', ('  ', '"world!"'), ')'),
            ],
            list(expression.Assign(
                left=MultilineLValue(),
                right=expression.BytesLiteral(b'hello world!', 6),
            ).render_expression())
        )

    def test_binary_operators(self):
        all_binary_operators = [
            cls for cls in vars(expression).values()
            if isinstance(cls, type) and issubclass(cls, expression.BinaryOperationExpression)
            and cls is not expression.BinaryOperationExpression
            and cls is not expression.Assign
        ]

        expected_operators = {
            expression.Multiply: '*',
            expression.Mod: '%',
            expression.Divide: '/',
            expression.Add: '+',
            expression.Subtract: '-',
            expression.ShiftLeft: '<<',
            expression.ShiftRight: '>>',
            expression.LessThan: '<',
            expression.GreaterThan: '>',
            expression.LessThanOrEqual: '<=',
            expression.GreaterThanOrEqual: '>=',
            expression.Equals: '==',
            expression.NotEquals: '!=',
            expression.BitwiseAnd: '&',
            expression.BitwiseOr: '|',
            expression.BitwiseXor: '^',
            expression.And: '&&',
            expression.Or: '||',
        }

        self.assertSetEqual(set(expected_operators.keys()), set(all_binary_operators))

        for cls, expected_operator in expected_operators.items():
            # noinspection PyArgumentList
            self.assertEqual(
                [
                    ('(', '123'),
                    ('  ', expected_operator, ' ', '456', ')'),
                ],
                list(cls(
                    left=expression.IntegerLiteral(123),
                    right=expression.IntegerLiteral(456),
                ).render_expression())
            )

            # noinspection PyArgumentList
            self.assertEqual(
                [
                    ('(', '"foo "'),
                    ('  ', '"bar"'),
                    ('  ', expected_operator, ' ', '"hello "'),
                    ('  ', ('  ', '"world!"'), ')'),
                ],
                list(cls(
                    left=expression.BytesLiteral(b'foo bar', 4),
                    right=expression.BytesLiteral(b'hello world!', 6),
                ).render_expression())
            )
