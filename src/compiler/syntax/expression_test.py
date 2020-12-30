import unittest

from . import expression


class ExpressionTestCase(unittest.TestCase):
    def test_has_yield(self):
        self.assertIs(
            True,
            expression.Yield().has_yield
        )

        self.assertIs(
            True,
            expression.YieldFrom().has_yield
        )

        self.assertIs(
            False,
            expression.Variable('foo').has_yield
        )

        # Check nesting works.
        self.assertIs(
            True,
            expression.Unpack([
                expression.Variable('a'),
                expression.Subscript(
                    operand=expression.Yield(),
                    subscript=expression.Variable('foo'),
                ),
            ]).has_yield
        )

        # Check even more nesting works.
        self.assertIs(
            True,
            expression.Unpack([
                expression.Variable('a'),
                expression.Subscript(
                    operand=expression.Variable('foo'),
                    subscript=expression.Subscript(
                        operand=expression.Variable('bar'),
                        subscript=expression.YieldFrom(),
                    ),
                ),
            ]).has_yield
        )


class UnpackTestCase(unittest.TestCase):
    def test_expressions(self):
        unpack = expression.Unpack([
            expression.Variable('a'),
            expression.Variable('b'),
        ])

        self.assertEqual(
            [
                expression.Variable('a'),
                expression.Variable('b'),
            ],
            list(unpack.expressions)
        )

    def test_variable_assignments(self):
        unpack = expression.Unpack([
            expression.Variable('a'),
            expression.Unpack([
                expression.Variable('b'),
                expression.Unpack([
                    expression.Variable('c'),
                    expression.Variable('d'),
                ]),
                expression.Variable('e'),
            ]),
            expression.Variable('f'),
        ])

        self.assertEqual(
            [
                expression.Variable('a'),
                expression.Variable('b'),
                expression.Variable('c'),
                expression.Variable('d'),
                expression.Variable('e'),
                expression.Variable('f'),
            ],
            list(unpack.variable_assignments)
        )


class SubscriptTestCase(unittest.TestCase):
    def test_expressions(self):
        subscript = expression.Subscript(
            operand=expression.Variable('my_array'),
            subscript=expression.Variable('my_index'),
        )

        self.assertEqual(
            [
                expression.Variable('my_array'),
                expression.Variable('my_index'),
            ],
            list(subscript.expressions)
        )


class DotTestCase(unittest.TestCase):
    def test_expressions(self):
        dot = expression.Dot(
            operand=expression.Variable('my_object'),
            member='foo',
        )

        self.assertEqual(
            [
                expression.Variable('my_object'),
            ],
            list(dot.expressions)
        )


class YieldTestCase(unittest.TestCase):
    def test_expressions(self):
        yield_expr = expression.Yield()

        self.assertEqual(
            [],
            list(yield_expr.expressions)
        )

        yield_expr = expression.Yield(
            expression=expression.Variable('foo')
        )

        self.assertEqual(
            [
                expression.Variable('foo')
            ],
            list(yield_expr.expressions)
        )


class YieldFromTestCase(unittest.TestCase):
    def test_expressions(self):
        yield_from_expr = expression.YieldFrom()

        self.assertEqual(
            [],
            list(yield_from_expr.expressions)
        )

        yield_from_expr = expression.YieldFrom(
            expression=expression.Variable('foo')
        )

        self.assertEqual(
            [
                expression.Variable('foo')
            ],
            list(yield_from_expr.expressions)
        )


class AwaitTestCase(unittest.TestCase):
    def test_expressions(self):
        await_expr = expression.Await()

        self.assertEqual(
            [],
            list(await_expr.expressions)
        )

        await_expr = expression.Await(
            expression=expression.Variable('foo')
        )

        self.assertEqual(
            [
                expression.Variable('foo')
            ],
            list(await_expr.expressions)
        )


class IfElseTestCase(unittest.TestCase):
    def test_expressions(self):
        if_else = expression.IfElse(
            condition=expression.Variable('condition'),
            value=expression.Variable('value'),
            else_value=expression.Variable('else_value'),
        )

        self.assertEqual(
            [
                expression.Variable('condition'),
                expression.Variable('value'),
                expression.Variable('else_value'),
            ],
            list(if_else.expressions)
        )


class ComprehensionTestCase(unittest.TestCase):
    def test_expressions(self):
        comprehension = expression.Comprehension(
            value=expression.Variable('value'),
            loops=[],
        )

        self.assertEqual(
            [
                expression.Variable('value'),
            ],
            list(comprehension.expressions)
        )

        comprehension = expression.Comprehension(
            value=expression.Variable('value'),
            loops=[
                expression.Comprehension.Loop(
                    iterable=expression.Variable('iterable'),
                    receiver=expression.Variable('receiver'),
                ),
            ],
            condition=expression.Variable('condition'),
        )

        self.assertEqual(
            [
                expression.Variable('iterable'),
                expression.Variable('receiver'),
                expression.Variable('value'),
                expression.Variable('condition'),
            ],
            list(comprehension.expressions)
        )
