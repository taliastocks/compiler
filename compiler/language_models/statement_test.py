import unittest

from . import statement, expression, function, class_, namespace as namespace_module
from ..libs import parser as parser_module

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
                expression.Variable('declaration'),
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
                    statement.Declaration(
                        expression.Variable('declaration')
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
                    statement.Declaration(
                        expression.Variable('some_other_variable')
                    ),
                ]),
            ).nonlocal_variables)
        )


class BlockTestCase(unittest.TestCase):
    def test_execute(self):
        namespace = namespace_module.Namespace()

        test_statement: statement.Statement = statement.Block.parse(  # noqa
            parser_module.Cursor([
                '    a = 1',
                '    b = 2',
            ])
        ).last_symbol
        outcome = test_statement.execute(namespace)

        self.assertIsInstance(outcome, statement.Statement.Success)
        self.assertEqual(1, namespace.lookup('a'))
        self.assertEqual(2, namespace.lookup('b'))

    def test_execute_exception(self):
        namespace = namespace_module.Namespace()
        test_statement: statement.Statement = statement.Block.parse(  # noqa
            parser_module.Cursor([
                '    a = 1',
                '    b',  # raise NameError
                '    c = 2',  # not reached
            ])
        ).last_symbol
        outcome: statement.Raise.Outcome = test_statement.execute(namespace)

        self.assertIsInstance(outcome, statement.Raise.Outcome)
        self.assertEqual(
            repr(NameError("name 'b' is not defined")),
            repr(outcome.exception)
        )
        self.assertEqual(1, namespace.lookup('a'))

        with self.assertRaisesRegex(KeyError, "no such name 'c'"):
            namespace.lookup('c')

        namespace = namespace_module.Namespace()
        namespace.declare('RuntimeError', RuntimeError)
        test_statement: statement.Statement = statement.Block.parse(  # noqa
            parser_module.Cursor([
                '    a = 1',
                '    raise RuntimeError("error!")',  # raise RuntimeError
                '    c = 2',  # not reached
            ])
        ).last_symbol
        outcome: statement.Raise.Outcome = test_statement.execute(namespace)

        self.assertIsInstance(outcome, statement.Raise.Outcome)
        self.assertEqual(
            repr(RuntimeError('error!')),
            repr(outcome.exception)
        )
        self.assertEqual(1, namespace.lookup('a'))

        with self.assertRaisesRegex(KeyError, "no such name 'c'"):
            namespace.lookup('c')

    def test_parse(self):
        self.assertEqual(
            statement.Block.parse(
                parser_module.Cursor([
                    '    foo',
                    '    bar',
                ])
            ).last_symbol,
            statement.Block([
                statement.Declaration(expression.Variable('foo')),
                statement.Declaration(expression.Variable('bar')),
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
                statement.Declaration(expression.Variable('foo')),
                statement.Declaration(expression.Variable('bar')),
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
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'a: b = c',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                expression.Variable(
                    name='a',
                    annotation=expression.Variable('b'),
                    initializer=expression.Variable('c'),
                )
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'a: b',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                expression.Variable(
                    name='a',
                    annotation=expression.Variable('b'),
                )
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'def foo():',
                    '    bar',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                function.Function(
                    name='foo',
                    body=statement.Block([
                        statement.Declaration(
                            expression.Variable('bar')
                        )
                    ]),
                )
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'class foo:',
                    '    bar',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                class_.Class(
                    name='foo',
                    body=statement.Block([
                        statement.Declaration(
                            expression.Variable('bar')
                        )
                    ]),
                )
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected variable annotation'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'a:'
                ])
            )

    def test_receivers(self):
        declaration = statement.Declaration(
            declarable=expression.Variable('foo')
        )

        self.assertEqual(
            [
                expression.Variable('foo')
            ],
            list(declaration.receivers)
        )


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
                    '(a) ='
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

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'a + b',
                    'next line',
                ])
            ).last_symbol,
            statement.Expression(
                expression.Add(
                    expression.Variable('a'),
                    expression.Variable('b'),
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
                    statement.Declaration(
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
                    statement.Declaration(
                        expression.Variable('b')
                    )
                ]),
                else_body=statement.Block([
                    statement.If(
                        condition=expression.Variable('c'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('d')
                            )
                        ]),
                        else_body=statement.Block([
                            statement.Declaration(
                                expression.Variable('e')
                            )
                        ])
                    )
                ])
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected an operand'):
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Declaration(
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Declaration(
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
                statement.Declaration(
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
                    statement.Declaration(
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
                    statement.Declaration(
                        expression.Variable('b')
                    )
                ]),
                else_body=statement.Block([
                    statement.If(
                        condition=expression.Variable('c'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('d')
                            )
                        ]),
                        else_body=statement.Block([
                            statement.Declaration(
                                expression.Variable('e')
                            )
                        ])
                    )
                ])
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected an operand'):
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Declaration(
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Declaration(
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
                statement.Declaration(
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
                    statement.Declaration(
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
                    statement.Declaration(
                        expression.Variable('b')
                    )
                ]),
                else_body=statement.Block([
                    statement.If(
                        condition=expression.Variable('c'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('d')
                            )
                        ]),
                        else_body=statement.Block([
                            statement.Declaration(
                                expression.Variable('e')
                            )
                        ])
                    )
                ])
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, 'expected LValue'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for 1',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'in\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'for a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Declaration(
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
                statement.Declaration(
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            else_body=statement.Block([
                statement.Declaration(
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
                statement.Declaration(
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
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'with context_manager as receiver:',
                    '    c',
                    'next line',
                ])
            ).last_symbol,
            statement.With(
                context_manager=expression.Variable('context_manager'),
                receiver=expression.Variable('receiver'),
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('c')
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'with context_manager:',
                    '    body',
                    'next line',
                ])
            ).last_symbol,
            statement.With(
                context_manager=expression.Variable('context_manager'),
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as b, c as d:',
                    '    body',
                    'next line',
                ])
            ).last_symbol,
            statement.With(
                context_manager=expression.Variable('a'),
                receiver=expression.Variable('b'),
                body=statement.Block([
                    statement.With(
                        context_manager=expression.Variable('c'),
                        receiver=expression.Variable('d'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('body')
                            )
                        ]),
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a, c as d:',
                    '    body',
                    'next line',
                ])
            ).last_symbol,
            statement.With(
                context_manager=expression.Variable('a'),
                body=statement.Block([
                    statement.With(
                        context_manager=expression.Variable('c'),
                        receiver=expression.Variable('d'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('body')
                            )
                        ]),
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as b, c:',
                    '    body',
                    'next line',
                ])
            ).last_symbol,
            statement.With(
                context_manager=expression.Variable('a'),
                receiver=expression.Variable('b'),
                body=statement.Block([
                    statement.With(
                        context_manager=expression.Variable('c'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('body')
                            )
                        ]),
                    )
                ]),
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, 'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'as\', \':\', \',\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected LValue'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as 3',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\', \',\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as b',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, 'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a,',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, 'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as b,',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as b:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as b, c as d:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as b:',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'with a as b, c as d:',
                ])
            )

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
                statement.Declaration(
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
                statement.Declaration(
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
                statement.Declaration(
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
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    body',
                    'except exception as receiver:',
                    '    exception_body',
                    'except exception_2:',
                    '    exception_body_2',
                    'else:',
                    '    else_body',
                    'finally:',
                    '    finally_body',
                    'next line',
                ])
            ).last_symbol,
            statement.Try(
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                exception_handlers=[
                    statement.Try.ExceptionHandler(
                        exception=expression.Variable('exception'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('exception_body')
                            )
                        ]),
                        receiver=expression.Variable('receiver'),
                    ),
                    statement.Try.ExceptionHandler(
                        exception=expression.Variable('exception_2'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('exception_body_2')
                            )
                        ]),
                    ),
                ],
                else_body=statement.Block([
                    statement.Declaration(
                        expression.Variable('else_body')
                    )
                ]),
                finally_body=statement.Block([
                    statement.Declaration(
                        expression.Variable('finally_body')
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    body',
                    'except exception as receiver:',
                    '    exception_body',
                    'next line',
                ])
            ).last_symbol,
            statement.Try(
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                exception_handlers=[
                    statement.Try.ExceptionHandler(
                        exception=expression.Variable('exception'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('exception_body')
                            )
                        ]),
                        receiver=expression.Variable('receiver'),
                    ),
                ],
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    body',
                    'except exception as receiver:',
                    '    exception_body',
                    'else:',
                    '    else_body',
                    'next line',
                ])
            ).last_symbol,
            statement.Try(
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                exception_handlers=[
                    statement.Try.ExceptionHandler(
                        exception=expression.Variable('exception'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('exception_body')
                            )
                        ]),
                        receiver=expression.Variable('receiver'),
                    ),
                ],
                else_body=statement.Block([
                    statement.Declaration(
                        expression.Variable('else_body')
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    body',
                    'except exception as receiver:',
                    '    exception_body',
                    'finally:',
                    '    finally_body',
                    'next line',
                ])
            ).last_symbol,
            statement.Try(
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                exception_handlers=[
                    statement.Try.ExceptionHandler(
                        exception=expression.Variable('exception'),
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('exception_body')
                            )
                        ]),
                        receiver=expression.Variable('receiver'),
                    ),
                ],
                finally_body=statement.Block([
                    statement.Declaration(
                        expression.Variable('finally_body')
                    )
                ]),
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    body',
                    'finally:',
                    '    finally_body',
                    'next line',
                ])
            ).last_symbol,
            statement.Try(
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                exception_handlers=[],
                finally_body=statement.Block([
                    statement.Declaration(
                        expression.Variable('finally_body')
                    )
                ]),
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'except\', \'else\', \'finally\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'as\', \':\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a as',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected LValue'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a as 3',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a as b',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a as b:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a as b:',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a:',
                    '    b',
                    'else',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a:',
                    '    b',
                    'else:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'except a:',
                    '    b',
                    'else:',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'finally',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'finally:a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'try:',
                    '    a',
                    'finally:',
                ])
            )

    def test_receiver(self):
        try_statement = statement.Try(
            body=statement.Block([
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            exception_handlers=[
                statement.Try.ExceptionHandler(
                    exception=expression.Variable('exception'),
                    body=statement.Block([
                        statement.Declaration(
                            expression.Variable('exception_body')
                        ),
                    ]),
                    receiver=expression.Variable('receiver'),
                ),
                statement.Try.ExceptionHandler(  # receiver is optional
                    exception=expression.Variable('exception'),
                    body=statement.Block([
                        statement.Declaration(
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            exception_handlers=[
                statement.Try.ExceptionHandler(
                    exception=expression.Variable('exception'),
                    receiver=expression.Variable('receiver'),
                    body=statement.Block([
                        statement.Declaration(
                            expression.Variable('exception_body')
                        ),
                    ]),
                )
            ],
            else_body=statement.Block([
                statement.Declaration(
                    expression.Variable('else_body')
                ),
            ]),
            finally_body=statement.Block([
                statement.Declaration(
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            exception_handlers=[
                statement.Try.ExceptionHandler(
                    exception=expression.Variable('exception'),
                    body=statement.Block([
                        statement.Declaration(
                            expression.Variable('exception_body')
                        ),
                    ]),
                    receiver=expression.Variable('receiver'),
                ),
                statement.Try.ExceptionHandler(  # receiver is optional
                    exception=expression.Variable('exception'),
                    body=statement.Block([
                        statement.Declaration(
                            expression.Variable('exception_body')
                        ),
                    ]),
                ),
            ],
            else_body=statement.Block([
                statement.Declaration(
                    expression.Variable('else_body')
                ),
            ]),
            finally_body=statement.Block([
                statement.Declaration(
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
                statement.Declaration(
                    expression.Variable('body')
                )
            ]),
            exception_handlers=[
                statement.Try.ExceptionHandler(
                    exception=expression.Variable('exception'),
                    receiver=expression.Variable('receiver'),
                    body=statement.Block([
                        statement.Declaration(
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
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'raise',
                    'next line',
                ])
            ).last_symbol,
            statement.Raise()
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'raise foo',
                    'next line',
                ])
            ).last_symbol,
            statement.Raise(expression=expression.Variable('foo'))
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'raise;',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'raise a a',
                ])
            )

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
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'return',
                    'next line',
                ])
            ).last_symbol,
            statement.Return()
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'return foo',
                    'next line',
                ])
            ).last_symbol,
            statement.Return(expression=expression.Variable('foo'))
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'return;',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'return a a',
                ])
            )

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


class NonlocalTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'nonlocal a',
                    'next line',
                ])
            ).last_symbol,
            statement.Nonlocal([
                expression.Variable('a')
            ])
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'nonlocal a, b',
                    'next line',
                ])
            ).last_symbol,
            statement.Nonlocal([
                expression.Variable('a'),
                expression.Variable('b'),
            ])
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Variable\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'nonlocal;',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\',\', EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'nonlocal a a',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Variable\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'nonlocal a,',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\',\', EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'nonlocal a, a a',
                ])
            )

    def test_expressions(self):
        nonlocal_statement = statement.Nonlocal(
            variables=[
                expression.Variable('foo'),
                expression.Variable('bar'),
            ]
        )

        self.assertEqual(
            [
                expression.Variable('foo'),
                expression.Variable('bar'),
            ],
            list(nonlocal_statement.expressions)
        )


class AssertTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'assert foo',
                    'next line',
                ])
            ).last_symbol,
            statement.Assert(expression=expression.Variable('foo'))
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'assert',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'assert a a',
                ])
            )

    def test_expressions(self):
        assert_statement = statement.Assert(
            expression=expression.Variable('foo')
        )

        self.assertEqual(
            [
                expression.Variable('foo')
            ],
            list(assert_statement.expressions)
        )


class PassTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'pass',
                    'next line',
                ])
            ).last_symbol,
            statement.Pass()
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'pass a',
                ])
            )

    def test_expressions(self):
        pass_statement = statement.Pass()

        self.assertEqual(
            [],
            list(pass_statement.expressions)
        )


class ImportTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'import foo',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                statement.Import(
                    name='foo',
                    path=['foo'],
                )
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'import foo.bar',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                statement.Import(
                    name='bar',
                    path=['foo', 'bar'],
                )
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'import .foo.bar',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                statement.Import(
                    name='bar',
                    path=['.', 'foo', 'bar'],
                )
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'import ...foo.bar',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                statement.Import(
                    name='bar',
                    path=['...', 'foo', 'bar'],
                )
            )
        )

        self.assertEqual(
            statement.Statement.parse(
                parser_module.Cursor([
                    'import ...foo.bar as baz',
                    'next line',
                ])
            ).last_symbol,
            statement.Declaration(
                statement.Import(
                    name='baz',
                    path=['...', 'foo', 'bar'],
                )
            )
        )

    def test_parse_error(self):
        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'.\', Identifier\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'import'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'.\', Identifier\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'import .'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Identifier\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'import .foo as'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            statement.Statement.parse(
                parser_module.Cursor([
                    'import .foo as bar garbage'
                ])
            )

    def test_expressions(self):
        import_statement = statement.Import(
            name='foo',
            path=['...', 'foo'],
        )

        self.assertEqual(
            [],
            list(import_statement.expressions)
        )
