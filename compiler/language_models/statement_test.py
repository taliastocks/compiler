import unittest

from . import statement, expression
from .. import parser as parser_module

# pylint: disable=fixme
# pylint: disable=too-many-lines


class StatementTestCase(unittest.TestCase):
    def test_variable_assignments(self):
        # Simple assignment returns variables.
        self.assertEqual(
            [
                expression.Variable('foo'),
                expression.Variable('bar'),
            ],
            list(statement.Assignment(
                receivers=[
                    expression.Variable('foo'),
                    expression.Variable('bar'),
                ],
                expression=expression.Variable('value'),
            ).variable_assignments)
        )

        # Nested statements with unpacking return nested variables.
        self.assertEqual(
            {
                expression.Variable('receiver_1'),
                expression.Variable('receiver_2'),
                expression.Variable('receiver_3'),
                expression.Variable('receiver_4'),
            },
            set(statement.For(
                iterable=expression.Variable('iterable'),
                receiver=expression.Unpack([
                    expression.Variable('receiver_1'),
                    expression.Unpack([
                        expression.Variable('receiver_2'),
                        expression.Variable('receiver_3'),
                    ]),
                ]),
                body=statement.Block([
                    statement.With(
                        context_manager=expression.Variable('context_manager'),
                        body=statement.Block([]),
                        receiver=expression.Variable('receiver_4'),
                    ),
                    statement.Expression(
                        expression.Variable('some_other_variable')
                    ),
                ]),
            ).variable_assignments)
        )

        # Assignments from expression.Assignment.
        self.assertEqual(
            [
                expression.Variable('assigned')
            ],
            list(statement.If(
                condition=expression.Equal(
                    left=expression.Assignment(
                        left=expression.Variable('assigned'),
                        right=expression.Variable('eq_left'),
                    ),
                    right=expression.Variable('eq_right'),
                ),
                body=statement.Block(),
            ).variable_assignments)
        )

    def test_nonlocal_variables(self):
        # Simple.
        self.assertEqual(
            [
                expression.Variable('my_nonlocal_1'),
                expression.Variable('my_nonlocal_2'),
            ],
            list(statement.Nonlocal([
                expression.Variable('my_nonlocal_1'),
                expression.Variable('my_nonlocal_2'),
            ]).nonlocal_variables)
        )

        # Nested.
        self.assertEqual(
            [
                expression.Variable('my_nonlocal'),
            ],
            list(statement.While(
                condition=expression.Variable('condition'),
                body=statement.Block([
                    statement.Nonlocal([
                        expression.Variable('my_nonlocal')
                    ]),
                    statement.Expression(
                        expression.Variable('some_other_variable')
                    ),
                ]),
            ).nonlocal_variables)
        )

    def test_has_yield(self):
        # Simple.
        self.assertIs(
            True,
            statement.Expression(
                expression.Yield()
            ).has_yield
        )
        self.assertIs(
            True,
            statement.Expression(
                expression.YieldFrom()
            ).has_yield
        )
        self.assertIs(
            False,
            statement.Expression(
                expression.Variable('whatever')
            ).has_yield
        )

        # Nested.
        self.assertIs(
            True,
            statement.While(
                condition=expression.Variable('condition'),
                body=statement.Block([]),
                else_body=statement.Block([
                    statement.Expression(
                        expression.Yield()
                    )
                ])
            ).has_yield
        )


class BlockTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Block.parse(
                parser_module.Cursor([
                    '    foo',
                    '    bar',
                ])
            ).last_symbol,
            statement.Block([
                statement.Expression(expression.Variable('foo')),
                statement.Expression(expression.Variable('bar')),
            ])
        )

        self.assertEqual(
            statement.Block.parse(
                parser_module.Cursor([
                    '    foo',
                    '    bar',
                    'baz',
                ])
            ).last_symbol,
            statement.Block([
                statement.Expression(expression.Variable('foo')),
                statement.Expression(expression.Variable('bar')),
            ])
        )

    def test_statements(self):
        inner_inner_block = statement.Block([])
        inner_block_1 = statement.Block([inner_inner_block])
        inner_block_2 = statement.Block([])
        block = statement.Block([inner_block_1, inner_block_2])

        self.assertEqual(
            [
                inner_block_1,
                inner_block_2,
                # inner_inner_block is not a direct descendant
            ],
            list(block.statements)
        )


class DeclarationTestCase(unittest.TestCase):
    pass


class AssignmentTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    '(a) = b = c',
                    'next line',
                ])
            ).last_symbol,
            statement.Assignment(
                receivers=[
                    expression.Unpack([
                        expression.Variable('a')
                    ]),
                    expression.Variable('b'),
                ],
                expression=expression.Variable('c'),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    '(a) = b =',
                    '    c',
                    'next line',
                ])
            ).last_symbol,
            statement.Assignment(
                receivers=[
                    expression.Unpack([
                        expression.Variable('a')
                    ]),
                    expression.Variable('b'),
                ],
                expression=expression.Variable('c'),
            )
        )

        with self.assertRaisesRegex(parser_module.ParseError, 'expected Expression'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'a ='
                ])
            )

    def test_receivers(self):
        # ``a = b = expr``
        assignment = statement.Assignment(
            receivers=[
                expression.Variable('a'),
                expression.Variable('b'),
            ],
            expression=expression.Variable('expr'),
        )

        self.assertEqual(
            [
                expression.Variable('a'),
                expression.Variable('b'),
            ],
            list(assignment.receivers)
        )

    def test_expressions(self):
        # ``a = b = expr``
        assignment = statement.Assignment(
            receivers=[
                expression.Variable('a'),
                expression.Variable('b'),
            ],
            expression=expression.Variable('expr'),
        )

        self.assertEqual(
            [
                expression.Variable('expr'),
                expression.Variable('a'),
                expression.Variable('b'),
            ],
            list(assignment.expressions)
        )


class ExpressionTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    '1 + 2',
                    'next line',
                ])
            ).last_symbol,
            statement.Expression(
                expression.Add(
                    expression.Number(1),
                    expression.Number(2),
                )
            )
        )

        with self.assertRaises(parser_module.ParseError):
            statement.Statement.parse(
                parser_module.Cursor([
                    '1 + 2 3',
                ])
            )

    def test_expressions(self):
        expr = statement.Expression(
            expression=expression.Variable('foo')
        )

        self.assertEqual(
            [
                expression.Variable('foo')
            ],
            list(expr.expressions)
        )


class IfTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'if a:',
                    '    b',
                    'next line',
                ])
            ).last_symbol,
            statement.If(
                condition=expression.Variable('a'),
                body=statement.Block([
                    statement.Expression(
                        expression.Variable('b')
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'if a:',
                    '    b',
                    'else if c:',
                    '    d',
                    'else:',
                    '    e',
                    'next line',
                ])
            ).last_symbol,
            statement.If(
                condition=expression.Variable('a'),
                body=statement.Block([
                    statement.Expression(
                        expression.Variable('b')
                    )
                ]),
                else_body=statement.Block([
                    statement.If(
                        condition=expression.Variable('c'),
                        body=statement.Block([
                            statement.Expression(
                                expression.Variable('d')
                            )
                        ]),
                        else_body=statement.Block([
                            statement.Expression(
                                expression.Variable('e')
                            )
                        ])
                    )
                ])
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected Expression'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'if :',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'if a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'if a:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'if a:',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\', If\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'if a:',
                    '    b',
                    'else',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'if a:',
                    '    b',
                    'else:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'if a:',
                    '    b',
                    'else:',
                ])
            )

    def test_expressions(self):
        if_else_statement = statement.If(
            condition=expression.Variable('condition'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Expression(
                    expression.Variable('else_body')
                )
            ]),
        )

        self.assertEqual(
            [
                expression.Variable('condition')
            ],
            list(if_else_statement.expressions)
        )

    def test_statements(self):
        if_else_statement = statement.If(
            condition=expression.Variable('condition'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Expression(
                    expression.Variable('else_body')
                )
            ]),
        )

        self.assertEqual(
            [
                if_else_statement.body,
                if_else_statement.else_body,
            ],
            list(if_else_statement.statements)
        )

        if_statement = statement.If(
            condition=expression.Variable('condition'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
        )

        self.assertEqual(
            [
                if_statement.body,
            ],
            list(if_statement.statements)
        )


class WhileTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'while a:',
                    '    b',
                    'next line',
                ])
            ).last_symbol,
            statement.While(
                condition=expression.Variable('a'),
                body=statement.Block([
                    statement.Expression(
                        expression.Variable('b')
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'while a:',
                    '    b',
                    'else if c:',
                    '    d',
                    'else:',
                    '    e',
                    'next line',
                ])
            ).last_symbol,
            statement.While(
                condition=expression.Variable('a'),
                body=statement.Block([
                    statement.Expression(
                        expression.Variable('b')
                    )
                ]),
                else_body=statement.Block([
                    statement.If(
                        condition=expression.Variable('c'),
                        body=statement.Block([
                            statement.Expression(
                                expression.Variable('d')
                            )
                        ]),
                        else_body=statement.Block([
                            statement.Expression(
                                expression.Variable('e')
                            )
                        ])
                    )
                ])
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected Expression'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'while :',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'while a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'while a:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'while a:',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\', If\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'while a:',
                    '    b',
                    'else',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'while a:',
                    '    b',
                    'else:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'while a:',
                    '    b',
                    'else:',
                ])
            )

    def test_expressions(self):
        while_statement = statement.While(
            condition=expression.Variable('condition'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Expression(
                    expression.Variable('else_body')
                )
            ]),
        )

        self.assertEqual(
            [
                expression.Variable('condition')
            ],
            list(while_statement.expressions)
        )

    def test_statements(self):
        while_statement = statement.While(
            condition=expression.Variable('condition'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Expression(
                    expression.Variable('else_body')
                )
            ]),
        )

        self.assertEqual(
            [
                while_statement.body,
                while_statement.else_body,
            ],
            list(while_statement.statements)
        )

        while_statement = statement.While(
            condition=expression.Variable('condition'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
        )

        self.assertEqual(
            [
                while_statement.body,
            ],
            list(while_statement.statements)
        )


class ForTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in iterable:',
                    '    b',
                    'next line',
                ])
            ).last_symbol,
            statement.For(
                receiver=expression.Variable('a'),
                iterable=expression.Variable('iterable'),
                body=statement.Block([
                    statement.Expression(
                        expression.Variable('b')
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in iterable:',
                    '    b',
                    'else if c:',
                    '    d',
                    'else:',
                    '    e',
                    'next line',
                ])
            ).last_symbol,
            statement.For(
                receiver=expression.Variable('a'),
                iterable=expression.Variable('iterable'),
                body=statement.Block([
                    statement.Expression(
                        expression.Variable('b')
                    )
                ]),
                else_body=statement.Block([
                    statement.If(
                        condition=expression.Variable('c'),
                        body=statement.Block([
                            statement.Expression(
                                expression.Variable('d')
                            )
                        ]),
                        else_body=statement.Block([
                            statement.Expression(
                                expression.Variable('e')
                            )
                        ])
                    )
                ])
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected LValue'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'in\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected Expression'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in iterable',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in iterable:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in iterable:',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\', If\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in iterable:',
                    '    b',
                    'else',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in iterable:',
                    '    b',
                    'else:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a in iterable:',
                    '    b',
                    'else:',
                ])
            )

    def test_expressions(self):
        for_statement = statement.For(
            iterable=expression.Variable('iterable'),
            receiver=expression.Variable('receiver'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Expression(
                    expression.Variable('else_body')
                )
            ]),
        )

        self.assertEqual(
            [
                expression.Variable('iterable'),
                expression.Variable('receiver'),
            ],
            list(for_statement.expressions)
        )

    def test_receivers(self):
        for_statement = statement.For(
            iterable=expression.Variable('iterable'),
            receiver=expression.Variable('receiver'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
        )

        self.assertEqual(
            [
                expression.Variable('receiver')
            ],
            list(for_statement.receivers)
        )

    def test_statements(self):
        for_statement = statement.For(
            iterable=expression.Variable('iterable'),
            receiver=expression.Variable('receiver'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Expression(
                    expression.Variable('else_body')
                )
            ]),
        )

        self.assertEqual(
            [
                for_statement.body,
                for_statement.else_body,
            ],
            list(for_statement.statements)
        )

        for_statement = statement.For(
            iterable=expression.Variable('iterable'),
            receiver=expression.Variable('receiver'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
        )

        self.assertEqual(
            [
                for_statement.body,
            ],
            list(for_statement.statements)
        )


class BreakTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'break',
                    'next line',
                ])
            ).last_symbol,
            statement.Break()
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'break a',
                ])
            )


class ContinueTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'continue',
                    'next line',
                ])
            ).last_symbol,
            statement.Continue()
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'continue a',
                ])
            )


class WithTestCase(unittest.TestCase):
    def test_receivers(self):
        with_statement = statement.With(
            context_manager=expression.Variable('context_manager'),
            body=statement.Block([]),
        )

        self.assertEqual(
            [],  # receiver omitted
            list(with_statement.receivers)
        )

        with_statement = statement.With(
            context_manager=expression.Variable('context_manager'),
            receiver=expression.Variable('receiver'),
            body=statement.Block([]),
        )

        self.assertEqual(
            [
                expression.Variable('receiver')
            ],
            list(with_statement.receivers)
        )

    def test_expressions(self):
        with_statement = statement.With(
            context_manager=expression.Variable('context_manager'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
        )

        self.assertEqual(
            [  # receiver omitted
                expression.Variable('context_manager'),
            ],
            list(with_statement.expressions)
        )

        with_statement = statement.With(
            context_manager=expression.Variable('context_manager'),
            receiver=expression.Variable('receiver'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
        )

        self.assertEqual(
            [
                expression.Variable('context_manager'),
                expression.Variable('receiver'),
            ],
            list(with_statement.expressions)
        )

    def test_statements(self):
        with_statement = statement.With(
            context_manager=expression.Variable('context_manager'),
            receiver=expression.Variable('receiver'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
        )

        self.assertEqual(
            [
                with_statement.body,
            ],
            list(with_statement.statements)
        )


class TryTestCase(unittest.TestCase):
    def test_receiver(self):
        try_statement = statement.Try(
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            exception_handlers=[
                statement.Try.ExceptionHandler(
                    exception=expression.Variable('exception'),
                    body=statement.Block([
                        statement.Expression(
                            expression.Variable('exception_body')
                        ),
                    ]),
                    receiver=expression.Variable('receiver'),
                ),
                statement.Try.ExceptionHandler(  # receiver is optional
                    exception=expression.Variable('exception'),
                    body=statement.Block([
                        statement.Expression(
                            expression.Variable('exception_body')
                        ),
                    ]),
                )
            ],
        )

        self.assertEqual(
            [
                expression.Variable('receiver')
            ],
            list(try_statement.receivers)
        )

    def test_expressions(self):
        try_else_finally_statement = statement.Try(
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            exception_handlers=[
                statement.Try.ExceptionHandler(
                    exception=expression.Variable('exception'),
                    receiver=expression.Variable('receiver'),
                    body=statement.Block([
                        statement.Expression(
                            expression.Variable('exception_body')
                        ),
                    ]),
                )
            ],
            else_body=statement.Block([
                statement.Expression(
                    expression.Variable('else_body')
                ),
            ]),
            finally_body=statement.Block([
                statement.Expression(
                    expression.Variable('finally_body')
                ),
            ]),
        )

        self.assertEqual(
            [
                expression.Variable('exception'),
                expression.Variable('receiver'),
            ],
            list(try_else_finally_statement.expressions)
        )

    def test_statements(self):
        try_else_finally_statement = statement.Try(
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            exception_handlers=[
                statement.Try.ExceptionHandler(
                    exception=expression.Variable('exception'),
                    body=statement.Block([
                        statement.Expression(
                            expression.Variable('exception_body')
                        ),
                    ]),
                    receiver=expression.Variable('receiver'),
                ),
                statement.Try.ExceptionHandler(  # receiver is optional
                    exception=expression.Variable('exception'),
                    body=statement.Block([
                        statement.Expression(
                            expression.Variable('exception_body')
                        ),
                    ]),
                ),
            ],
            else_body=statement.Block([
                statement.Expression(
                    expression.Variable('else_body')
                ),
            ]),
            finally_body=statement.Block([
                statement.Expression(
                    expression.Variable('finally_body')
                ),
            ]),
        )

        self.assertEqual(
            [
                try_else_finally_statement.body,
                try_else_finally_statement.exception_handlers[0].body,
                try_else_finally_statement.exception_handlers[1].body,
                try_else_finally_statement.else_body,
                try_else_finally_statement.finally_body,
            ],
            list(try_else_finally_statement.statements)
        )

        try_statement = statement.Try(
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
            exception_handlers=[
                statement.Try.ExceptionHandler(
                    exception=expression.Variable('exception'),
                    receiver=expression.Variable('receiver'),
                    body=statement.Block([
                        statement.Expression(
                            expression.Variable('exception_body')
                        ),
                    ]),
                )
            ],
        )

        self.assertEqual(
            [
                try_statement.body,
                try_statement.exception_handlers[0].body,
            ],
            list(try_statement.statements)
        )


class RaiseTestCase(unittest.TestCase):
    def test_expressions(self):
        raise_statement = statement.Raise(
            expression=expression.Variable('foo')
        )

        self.assertEqual(
            [
                expression.Variable('foo')
            ],
            list(raise_statement.expressions)
        )


class ReturnTestCase(unittest.TestCase):
    def test_expressions(self):
        return_statement = statement.Return(
            expression=expression.Variable('foo')
        )

        self.assertEqual(
            [
                expression.Variable('foo')
            ],
            list(return_statement.expressions)
        )
