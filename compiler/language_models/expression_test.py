import unittest

import attr

from . import expression as expression_module
from .. import parser as parser_module


class ExpressionTestCase(unittest.TestCase):
    def test_has_yield(self):
        self.assertIs(
            True,
            expression_module.Yield().has_yield
        )

        self.assertIs(
            True,
            expression_module.YieldFrom().has_yield
        )

        self.assertIs(
            False,
            expression_module.Variable('foo').has_yield
        )

        # Check nesting works.
        self.assertIs(
            True,
            expression_module.Unpack([
                expression_module.Variable('a'),
                expression_module.Subscript(
                    operand=expression_module.Yield(),
                    subscript=expression_module.Variable('foo'),
                ),
            ]).has_yield
        )

        # Check even more nesting works.
        self.assertIs(
            True,
            expression_module.Unpack([
                expression_module.Variable('a'),
                expression_module.Subscript(
                    operand=expression_module.Variable('foo'),
                    subscript=expression_module.Subscript(
                        operand=expression_module.Variable('bar'),
                        subscript=expression_module.YieldFrom(),
                    ),
                ),
            ]).has_yield
        )


class VariableTestCase(unittest.TestCase):
    def test_parse(self):
        @attr.s(frozen=True, slots=True)
        class ExpressionAnnotation(expression_module.Variable.Annotation):
            """Annotation which holds arbitrary expressions.
            """
            expression: expression_module.Expression = attr.ib()

            @classmethod
            def parse(cls, cursor):
                cursor = cursor.parse([
                    expression_module.Expression
                ])
                if isinstance(cursor.last_symbol, expression_module.Expression):
                    return cursor.new_from_symbol(cls(
                        expression=cursor.last_symbol
                    ))
                raise RuntimeError('this should be unreachable')

        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable: annotation1 annotation2 = other_variable']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable: annotation1 annotation2 = other_variable'],
                column=50,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotations=(
                        ExpressionAnnotation(
                            expression=expression_module.Variable(
                                name='annotation1'
                            )
                        ),
                        ExpressionAnnotation(
                            expression=expression_module.Variable(
                                name='annotation2'
                            )
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
                    lines=['variable:annotation1 annotation2=other_variable']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable:annotation1 annotation2=other_variable'],
                column=47,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotations=(
                        ExpressionAnnotation(
                            expression=expression_module.Variable(
                                name='annotation1'
                            )
                        ),
                        ExpressionAnnotation(
                            expression=expression_module.Variable(
                                name='annotation2'
                            )
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
                    lines=['variable  :  annotation1  annotation2  =  other_variable']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable  :  annotation1  annotation2  =  other_variable'],
                column=56,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotations=(
                        ExpressionAnnotation(
                            expression=expression_module.Variable(
                                name='annotation1'
                            )
                        ),
                        ExpressionAnnotation(
                            expression=expression_module.Variable(
                                name='annotation2'
                            )
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
                allowed_annotations=[ExpressionAnnotation],
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

        # Initializers are optional.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable: annotation1 annotation2']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable: annotation1 annotation2'],
                column=33,
                last_symbol=expression_module.Variable(
                    name='variable',
                    annotations=(
                        ExpressionAnnotation(
                            expression=expression_module.Variable(
                                name='annotation1'
                            )
                        ),
                        ExpressionAnnotation(
                            expression=expression_module.Variable(
                                name='annotation2'
                            )
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
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
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
            [
                expression_module.Variable('a'),
                expression_module.Variable('b'),
                expression_module.Variable('c'),
                expression_module.Variable('d'),
                expression_module.Variable('e'),
                expression_module.Variable('f'),
            ],
            list(unpack.variable_assignments)
        )


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


class ParenthesizedTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class DictionaryTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class SetTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class ListTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class CallTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class DotTestCase(unittest.TestCase):
    def test_expressions(self):
        dot = expression_module.Dot(
            operand=expression_module.Variable('my_object'),
            member='foo',
        )

        self.assertEqual(
            [
                expression_module.Variable('my_object'),
            ],
            list(dot.expressions)
        )


class SubscriptTestCase(unittest.TestCase):
    def test_expressions(self):
        subscript = expression_module.Subscript(
            operand=expression_module.Variable('my_array'),
            subscript=expression_module.Variable('my_index'),
        )

        self.assertEqual(
            [
                expression_module.Variable('my_array'),
                expression_module.Variable('my_index'),
            ],
            list(subscript.expressions)
        )


class AwaitTestCase(unittest.TestCase):
    def test_expressions(self):
        await_expr = expression_module.Await()

        self.assertEqual(
            [],
            list(await_expr.expressions)
        )

        await_expr = expression_module.Await(
            expression=expression_module.Variable('foo')
        )

        self.assertEqual(
            [
                expression_module.Variable('foo')
            ],
            list(await_expr.expressions)
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


class DivideTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class FloorDivideTestCase(unittest.TestCase):
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


class IsTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class IsNotTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class LessThanTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class LessThanOrEqualTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class GreaterThanTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class GreaterThanOrEqualTestCase(unittest.TestCase):
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
            value=expression_module.Variable('value'),
            else_value=expression_module.Variable('else_value'),
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


class AssignmentTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class YieldTestCase(unittest.TestCase):
    def test_expressions(self):
        yield_expr = expression_module.Yield()

        self.assertEqual(
            [],
            list(yield_expr.expressions)
        )

        yield_expr = expression_module.Yield(
            expression=expression_module.Variable('foo')
        )

        self.assertEqual(
            [
                expression_module.Variable('foo')
            ],
            list(yield_expr.expressions)
        )


class YieldFromTestCase(unittest.TestCase):
    def test_expressions(self):
        yield_from_expr = expression_module.YieldFrom()

        self.assertEqual(
            [],
            list(yield_from_expr.expressions)
        )

        yield_from_expr = expression_module.YieldFrom(
            expression=expression_module.Variable('foo')
        )

        self.assertEqual(
            [
                expression_module.Variable('foo')
            ],
            list(yield_from_expr.expressions)
        )
