import unittest

import attr

from . import expression as expression_module
from .. import parser as parser_module

# pylint: disable=fixme


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
                    subscriptable=expression_module.Yield(),
                    expression_arguments=[expression_module.Variable('foo')],
                ),
            ]).has_yield
        )

        # Check even more nesting works.
        self.assertIs(
            True,
            expression_module.Unpack([
                expression_module.Variable('a'),
                expression_module.Subscript(
                    subscriptable=expression_module.Variable('foo'),
                    expression_arguments=[expression_module.Subscript(
                        subscriptable=expression_module.Variable('bar'),
                        expression_arguments=[expression_module.YieldFrom()],
                    )],
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
                cursor = expression_module.ExpressionParser.parse(cursor)
                if not cursor:
                    return None
                if isinstance(cursor.last_symbol, expression_module.Expression):
                    return cursor.new_from_symbol(cls(
                        expression=cursor.last_symbol
                    ))
                raise RuntimeError('this should be unreachable')

        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable: annotation1, annotation2 = other_variable']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable: annotation1, annotation2 = other_variable'],
                column=51,
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
                    lines=['variable:annotation1,annotation2=other_variable']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable:annotation1,annotation2=other_variable'],
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

        # Trailing comma.
        self.assertEqual(
            expression_module.Variable.parse(
                parser_module.Cursor(
                    lines=['variable: annotation1, annotation2, = other_variable']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable: annotation1, annotation2, = other_variable'],
                column=52,
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
                    lines=['variable  :  annotation1 , annotation2  =  other_variable']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable  :  annotation1 , annotation2  =  other_variable'],
                column=57,
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
                    lines=['variable: annotation1, annotation2']
                ),
                allowed_annotations=[ExpressionAnnotation],
                parse_initializer=True,
            ),
            parser_module.Cursor(
                lines=['variable: annotation1, annotation2'],
                column=34,
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


class OperatorTestCase(unittest.TestCase):
    def test_operator_precedence(self):
        expected_precedence = (
            (expression_module.Call, expression_module.Dot, expression_module.Subscript),
            (expression_module.Await,),
            (expression_module.Exponentiation,),
            (expression_module.Positive, expression_module.Negative, expression_module.BitInverse),
            (expression_module.Multiply, expression_module.MatrixMultiply, expression_module.Divide,
                expression_module.FloorDivide, expression_module.Modulo),
            (expression_module.Add, expression_module.Subtract),
            (expression_module.ShiftLeft, expression_module.ShiftRight),
            (expression_module.BitAnd,),
            (expression_module.BitXor,),
            (expression_module.BitOr,),
            (expression_module.In, expression_module.NotIn, expression_module.Is, expression_module.IsNot,
                expression_module.LessThan, expression_module.LessThanOrEqual, expression_module.GreaterThan,
                expression_module.GreaterThanOrEqual, expression_module.NotEqual, expression_module.Equal),
            (expression_module.Not,),
            (expression_module.And,),
            (expression_module.Or,),
            (expression_module.IfElse,),
            (expression_module.Lambda,),
            (expression_module.Assignment,),
            (expression_module.Yield, expression_module.YieldFrom),
            (expression_module.Star, expression_module.StarStar),
            (expression_module.Slice,),
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
            expression_module.Call.precedes_on_right(expression_module.Await)
        )
        self.assertIs(
            False,
            expression_module.Await.precedes_on_right(expression_module.Call)
        )

        # Most operators should evaluate left to right.
        self.assertIs(
            False,
            expression_module.Await.precedes_on_right(expression_module.Await)
        )

        # ...with the exception of exponentiation...
        self.assertIs(
            True,
            expression_module.Exponentiation.precedes_on_right(expression_module.Exponentiation)
        )


class CallTestCase(unittest.TestCase):
    def test_expressions(self):
        call = expression_module.Call(
            callable=expression_module.Variable('my_function'),
            expression_arguments=[
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
    def test_expressions(self):
        subscript = expression_module.Subscript(
            subscriptable=expression_module.Variable('my_function'),
            expression_arguments=[
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


class StarStarTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class StarTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class SliceTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class CommaTestCase(unittest.TestCase):
    def test_expressions(self):
        pass


class ExpressionParser(unittest.TestCase):
    def test_parse(self):
        pass  # TODO: thoroughly test operator precedence parsing
