import unittest

from . import statement, expression


class StatementTestCase(unittest.TestCase):
    def test_variable_assignments(self):
        pass

    def test_nonlocal_variables(self):
        pass

    def test_has_yield(self):
        pass


class BlockTestCase(unittest.TestCase):
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


class AssignmentTestCase(unittest.TestCase):
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
