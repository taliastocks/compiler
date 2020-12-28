import unittest

from . import statement, expression


class BlockTestCase(unittest.TestCase):
    def test_linearize(self):
        inner_inner_block = statement.Block([])
        inner_block_1 = statement.Block([inner_inner_block])
        inner_block_2 = statement.Block([])
        block = statement.Block([inner_block_1, inner_block_2])

        self.assertEqual(
            [
                inner_inner_block,  # Inner-most block first.
                inner_block_1,
                inner_block_2,
            ],
            list(block.linearize())
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
            assignment.receivers
        )


class IfTestCase(unittest.TestCase):
    def test_linearize(self):
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
                statement.Expression(
                    expression.Variable('body')
                ),
                if_else_statement.body,
                statement.Expression(
                    expression.Variable('else_body')
                ),
                if_else_statement.else_body,
            ],
            list(if_else_statement.linearize())
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
                statement.Expression(
                    expression.Variable('body')
                ),
                if_statement.body,
            ],
            list(if_statement.linearize())
        )


class WhileTestCase(unittest.TestCase):
    def test_linearize(self):
        while_else_statement = statement.While(
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
                statement.Expression(
                    expression.Variable('body')
                ),
                while_else_statement.body,
                statement.Expression(
                    expression.Variable('else_body')
                ),
                while_else_statement.else_body,
            ],
            list(while_else_statement.linearize())
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
                statement.Expression(
                    expression.Variable('body')
                ),
                while_statement.body,
            ],
            list(while_statement.linearize())
        )


class ForTestCase(unittest.TestCase):
    def test_linearize(self):
        for_else_statement = statement.For(
            iterable=expression.Variable('condition'),
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
                statement.Expression(
                    expression.Variable('body')
                ),
                for_else_statement.body,
                statement.Expression(
                    expression.Variable('else_body')
                ),
                for_else_statement.else_body,
            ],
            list(for_else_statement.linearize())
        )

        for_statement = statement.For(
            iterable=expression.Variable('condition'),
            receiver=expression.Variable('receiver'),
            body=statement.Block([
                statement.Expression(
                    expression.Variable('body')
                )
            ]),
        )

        self.assertEqual(
            [
                statement.Expression(
                    expression.Variable('body')
                ),
                for_statement.body,
            ],
            list(for_statement.linearize())
        )

    def test_receiver(self):
        for_statement = statement.For(
            iterable=expression.Variable('condition'),
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
            for_statement.receivers
        )


class WithTestCase(unittest.TestCase):
    def test_linearize(self):
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
                statement.Expression(
                    expression.Variable('body')
                ),
                with_statement.body,
            ],
            list(with_statement.linearize())
        )

    def test_receiver(self):
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
                expression.Variable('receiver')
            ],
            with_statement.receivers
        )


class TryTestCase(unittest.TestCase):
    def test_linearize(self):
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
                statement.Expression(
                    expression.Variable('body')
                ),
                try_else_finally_statement.body,
                statement.Expression(
                    expression.Variable('exception_body')
                ),
                try_else_finally_statement.exception_handlers[0].body,
                statement.Expression(
                    expression.Variable('else_body')
                ),
                try_else_finally_statement.else_body,
                statement.Expression(
                    expression.Variable('finally_body')
                ),
                try_else_finally_statement.finally_body,
            ],
            list(try_else_finally_statement.linearize())
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
                statement.Expression(
                    expression.Variable('body')
                ),
                try_statement.body,
                statement.Expression(
                    expression.Variable('exception_body')
                ),
                try_statement.exception_handlers[0].body,
            ],
            list(try_statement.linearize())
        )

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
                expression.Variable('receiver')
            ],
            try_statement.receivers
        )
