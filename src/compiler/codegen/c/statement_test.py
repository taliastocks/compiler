import unittest

from . import statement, expression
from .types import integer


class StatementTestCase(unittest.TestCase):
    def test_declaration_statement(self):
        self.assertEqual(
            [
                ('int', ' ', 'foo', ';'),
            ],
            list(statement.DeclarationStatement(name='foo', type=integer.Int()).render_statement())
        )

    def test_expression_statement(self):
        self.assertEqual(
            [
                ('"hello"', ';'),
            ],
            list(statement.ExpressionStatement(expression.BytesLiteral(b'hello')).render_statement())
        )
        self.assertEqual(
            [
                '"hello "',
                (('  ', '"world!"'), ';'),
            ],
            list(statement.ExpressionStatement(
                expression.BytesLiteral(b'hello world!', chunk_size=6)
            ).render_statement())
        )
        self.assertEqual(
            [
                '"hello "',
                ('  ', '"there "'),
                (('  ', '"world!"'), ';'),
            ],
            list(statement.ExpressionStatement(
                expression.BytesLiteral(b'hello there world!', chunk_size=6)
            ).render_statement())
        )

    def test_return_statement(self):
        self.assertEqual(
            [
                'return;',
            ],
            list(statement.ReturnStatement().render_statement())
        )
        self.assertEqual(
            [
                ('return ', '"hello"', ';'),
            ],
            list(statement.ReturnStatement(expression.BytesLiteral(b'hello')).render_statement())
        )
        self.assertEqual(
            [
                ('return ', '"hello "'),
                (('  ', '"world!"'), ';'),
            ],
            list(statement.ReturnStatement(
                expression.BytesLiteral(b'hello world!', chunk_size=6)
            ).render_statement())
        )
        self.assertEqual(
            [
                ('return ', '"hello "'),
                ('  ', '"there "'),
                (('  ', '"world!"'), ';'),
            ],
            list(statement.ReturnStatement(
                expression.BytesLiteral(b'hello there world!', chunk_size=6)
            ).render_statement())
        )

    def test_continue_statement(self):
        self.assertEqual(
            [
                'continue;',
            ],
            list(statement.ContinueStatement().render_statement())
        )

    def test_break_statement(self):
        self.assertEqual(
            [
                'break;',
            ],
            list(statement.BreakStatement().render_statement())
        )

    def test_block_statement(self):
        self.assertEqual(
            [
                '{',
                '}',
            ],
            list(statement.BlockStatement([]).render_statement())
        )
        self.assertEqual(
            [
                '{',
                ('  ', 'return;'),
                '}',
            ],
            list(statement.BlockStatement([
                statement.ReturnStatement()
            ]).render_statement())
        )
        self.assertEqual(
            [
                '{',
                ('  ', 'return;'),
                ('  ', ('return ', '"hello "')),
                ('  ', ('  ', '"there "')),
                ('  ', (('  ', '"world!"'), ';')),
                '}',
            ],
            list(statement.BlockStatement([
                statement.ReturnStatement(),
                statement.ReturnStatement(
                    expression.BytesLiteral(b'hello there world!', chunk_size=6)
                ),
            ]).render_statement())
        )

    def test_if_statement(self):
        self.assertEqual(
            [
                'if (',
                ('  ', '42'),
                (') ', 'return;'),
                ('else ', ('13', ';')),
            ],
            list(statement.IfStatement(
                condition=expression.IntegerLiteral(42),
                if_true=statement.ReturnStatement(),
                if_false=statement.ExpressionStatement(expression.IntegerLiteral(13)),
            ).render_statement())
        )

        self.assertEqual(
            [
                'if (',
                ('  ', '42'),
                (') ', '{'),
                '}',
                ('else ', '{'),
                '}',
            ],
            list(statement.IfStatement(
                condition=expression.IntegerLiteral(42),
                if_true=statement.BlockStatement([]),
                if_false=statement.BlockStatement([]),
            ).render_statement())
        )

        self.assertEqual(
            [
                'if (',
                ('  ', '42'),
                (') ', 'return;'),
            ],
            list(statement.IfStatement(
                condition=expression.IntegerLiteral(42),
                if_true=statement.ReturnStatement(),
            ).render_statement())
        )

    def test_while_statement(self):
        self.assertEqual(
            [
                'while (',
                ('  ', '42'),
                (') ', 'return;'),
            ],
            list(statement.WhileStatement(
                condition=expression.IntegerLiteral(42),
                body=statement.ReturnStatement(),
            ).render_statement())
        )

        self.assertEqual(
            [
                'while (',
                ('  ', '42'),
                (') ', '{'),
                '}'
            ],
            list(statement.WhileStatement(
                condition=expression.IntegerLiteral(42),
                body=statement.BlockStatement([]),
            ).render_statement())
        )

    def test_do_while_statement(self):
        self.assertEqual(
            [
                ('do', 'return;'),
                'while (',
                ('  ', '42'),
                ');',
            ],
            list(statement.DoWhileStatement(
                condition=expression.IntegerLiteral(42),
                body=statement.ReturnStatement(),
            ).render_statement())
        )

        self.assertEqual(
            [
                ('do', '{'),
                '}',
                'while (',
                ('  ', '42'),
                ');',
            ],
            list(statement.DoWhileStatement(
                condition=expression.IntegerLiteral(42),
                body=statement.BlockStatement([]),
            ).render_statement())
        )

    def test_switch_statement(self):
        self.assertEqual(
            [
                'switch (',
                ('  ', '42'),
                ') {',
                ('  ', 'case ', '1', ':'),
                ('  ', 'case ', '2', ':'),
                ('  ', 'case ', '3', ':'),
                ('  ', '  ', 'return;'),
                ('  ', '  ', 'break;'),
                ('  ', 'case ', '4', ':'),
                ('  ', '  ', '{'),
                ('  ', '  ', '}'),
                ('  ', '  ', 'break;'),
                '}',
            ],
            list(statement.SwitchStatement(
                switch=expression.IntegerLiteral(42),
                cases=[
                    statement.SwitchStatement.Case(
                        values=[
                            expression.IntegerLiteral(3),
                            expression.IntegerLiteral(2),
                            expression.IntegerLiteral(1),
                        ],
                        consequence=statement.ReturnStatement(),
                    ),
                    statement.SwitchStatement.Case(
                        values=[
                            expression.IntegerLiteral(4),
                        ],
                        consequence=statement.BlockStatement([]),
                    ),
                ],
            ).render_statement())
        )

        self.assertEqual(
            [
                'switch (',
                ('  ', '42'),
                ') {',
                ('  ', 'case ', '1', ':'),
                ('  ', 'case ', '2', ':'),
                ('  ', 'case ', '3', ':'),
                ('  ', '  ', 'return;'),
                ('  ', '  ', 'break;'),
                ('  ', 'case ', '4', ':'),
                ('  ', '  ', '{'),
                ('  ', '  ', '}'),
                ('  ', '  ', 'break;'),
                ('  ', 'default:'),
                ('  ', '  ', '{'),
                ('  ', '  ', ('  ', 'return;')),
                ('  ', '  ', '}'),
                '}',
            ],
            list(statement.SwitchStatement(
                switch=expression.IntegerLiteral(42),
                cases=[
                    statement.SwitchStatement.Case(
                        values=[
                            expression.IntegerLiteral(3),
                            expression.IntegerLiteral(2),
                            expression.IntegerLiteral(1),
                        ],
                        consequence=statement.ReturnStatement(),
                    ),
                    statement.SwitchStatement.Case(
                        values=[
                            expression.IntegerLiteral(4),
                        ],
                        consequence=statement.BlockStatement([]),
                    ),
                ],
                default=statement.BlockStatement([statement.ReturnStatement()])
            ).render_statement())
        )
