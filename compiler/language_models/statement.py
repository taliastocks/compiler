from __future__ import annotations

import abc
import typing

import attr

from . import expression as expression_module
from .. import parser as parser_module

# pylint: disable=fixme


@attr.s
class Statement(parser_module.Symbol, metaclass=abc.ABCMeta):
    """A statement represents some action to be carried out.
    """
    @property
    def receivers(self) -> typing.Iterable[expression_module.LValue]:
        """Get all the LValues this statement assigns to, not including
        assignments performed by statements within this statement.
        """
        yield from []

    @property
    def expressions(self) -> typing.Iterable[expression_module.Expression]:
        """Get all the Expressions this statement executes, not including
        expressions executed by statements within this statement, and not
        including expressions within those expressions.
        """
        yield from []

    @property
    def statements(self) -> typing.Iterable[Statement]:
        """Get all the statements within this statement, not including
        statements within those statements.
        """
        yield from []

    @property
    def variable_assignments(self) -> typing.Iterable[expression_module.Variable]:
        """Get all the variable assignments that result from executing this statement.
        """
        for lvalue in self.receivers:
            if isinstance(lvalue, expression_module.Variable):
                yield lvalue

        for expr in self.expressions:
            yield from expr.variable_assignments

        for statement in self.statements:
            yield from statement.variable_assignments

    @property
    def nonlocal_variables(self) -> typing.Iterable[expression_module.Variable]:
        """Get all the ``nonlocal`` variable declarations.
        """
        if isinstance(self, Nonlocal):
            self: Nonlocal
            yield from self.variables

        for statement in self.statements:
            yield from statement.nonlocal_variables

    @property
    def has_yield(self) -> bool:
        """True if the statement yields, otherwise False.
        """
        for expression in self.expressions:
            if expression.has_yield:
                return True

        for statement in self.statements:
            if statement.has_yield:
                return True

        return False

    @classmethod
    def parse(cls, cursor):
        return cursor.parse_one_symbol([
            If,
            While,
            For,
            With,
            Try,
            Break,
            Continue,
            Raise,
            Return,
            Nonlocal,
            Declaration,
            Assignment,
            Expression,
        ])


@attr.s(frozen=True, slots=True)
class Block(Statement):
    """A sequence of statements to be executed in order.
    """
    statements: typing.Sequence[Statement] = attr.ib(converter=tuple, factory=list)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.BeginBlock,
        ])

        statements: list[Statement] = []
        while True:
            cursor = cursor.parse_one_symbol([
                parser_module.EndBlock,
                Statement,
            ])

            if isinstance(cursor.last_symbol, Statement):
                statements.append(cursor.last_symbol)
            else:  # EndBlock
                break

        return cursor.new_from_symbol(cls(
            cursor=cursor,
            statements=statements,
        ))


@attr.s(frozen=True, slots=True)
class Declaration(Statement):
    """An inline declaration, e.g. of a function, class, or variable.
    """
    declarable: declarable.Declarable = attr.ib()

    @classmethod
    def parse(cls, cursor):
        pass


@attr.s(frozen=True, slots=True)
class Assignment(Statement):
    """An assignment statement, e.g. ``foo = 3`` or ``foo = bar = 42``.
    """
    receivers: typing.Sequence[expression_module.LValue] = attr.ib(converter=tuple)
    expression: expression_module.Expression = attr.ib()

    @classmethod
    def parse(cls, cursor):
        cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
            parser_module.EndLine
        ])

        if not cursor or not isinstance(cursor.last_symbol, expression_module.Expression):
            return None  # No match.

        receivers: list[expression_module.LValue] = []

        try:
            receivers.append(expression_module.LValue.from_expression(cursor.last_symbol))
        except parser_module.ParseError:
            return None  # First symbol was not an LValue.

        cursor = cursor.parse_one_symbol([
            parser_module.EndLine,
            parser_module.Characters['=']
        ])

        if isinstance(cursor.last_symbol, parser_module.EndLine):
            return None  # End of line reached before assignment. No match.

        while True:
            cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.EndLine
            ])

            if not cursor or not isinstance(cursor.last_symbol, expression_module.Expression):
                raise parser_module.ParseError('expected Expression', cursor)

            expression = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.EndLine,
                parser_module.Characters['='],
            ])

            if isinstance(cursor.last_symbol, parser_module.EndLine):
                break  # End of statement.

            # Otherwise, we expect another expression, and the last expression was a receiver.
            receivers.append(expression_module.LValue.from_expression(expression))

        return cursor.new_from_symbol(cls(
            cursor=cursor,
            receivers=receivers,
            expression=expression,
        ))

    @property
    def expressions(self):
        yield self.expression

        for receiver in self.receivers:
            yield receiver


@attr.s(frozen=True, slots=True)
class Expression(Statement):
    """A statement that consists of a single expression.

    Not to be confused with ``expression.Expression``, which represents an expression itself.
    """
    expression: expression_module.Expression = attr.ib()

    @classmethod
    def parse(cls, cursor):
        cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
            parser_module.EndLine,
        ])

        if not cursor or not isinstance(cursor.last_symbol, expression_module.Expression):
            return None  # No match.

        expression = cursor.last_symbol

        cursor = cursor.parse_one_symbol([
            parser_module.EndLine,
        ], fail=True)

        return cursor.new_from_symbol(cls(
            cursor=cursor,
            expression=expression,
        ))

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class If(Statement):
    """Represents a conditional statement. If the condition is "truthy", execute the statements
    in ``body``. Otherwise, execute the statements in ``else_body`` (if provided).
    """
    condition: expression_module.Expression = attr.ib()
    body: Block = attr.ib()
    else_body: typing.Optional[Block] = attr.ib(default=None)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['if']
        ])

        cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
            parser_module.Characters[':']
        ], fail=True)

        condition = cursor.last_symbol

        cursor = cursor.parse_one_symbol([
            parser_module.Characters[':']
        ], fail=True).parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, Block)
        body = cursor.last_symbol

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['else'],
            parser_module.Always,
        ])

        if isinstance(cursor.last_symbol, parser_module.Always):
            return cursor.new_from_symbol(cls(
                cursor=cursor,
                condition=condition,
                body=body,
            ))

        cursor = cursor.parse_one_symbol([
            parser_module.Characters[':'],
            If,
        ], fail=True)

        if isinstance(cursor.last_symbol, If):
            return cursor.new_from_symbol(cls(
                cursor=cursor,
                condition=condition,
                body=body,
                else_body=Block([
                    cursor.last_symbol
                ]),
            ))

        cursor = cursor.parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, Block)
        return cursor.new_from_symbol(cls(
            cursor=cursor,
            condition=condition,
            body=body,
            else_body=cursor.last_symbol,
        ))

    @property
    def expressions(self):
        yield self.condition

    @property
    def statements(self):
        yield self.body

        if self.else_body is not None:
            yield self.else_body


@attr.s(frozen=True, slots=True)
class While(Statement):
    """Represents a while loop. While the condition is "truthy", execute the statements
    in ``body``. If the loop condition is (or becomes) "falsy", execute the statements
    in ``else_body`` (if provided). (If the loop body executes a ``Break`` statement,
    the ``else_body`` is not executed.)
    """
    condition: expression_module.Expression = attr.ib()
    body: Block = attr.ib()
    else_body: typing.Optional[Block] = attr.ib(default=None)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['while']
        ])

        cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
            parser_module.Characters[':']
        ], fail=True)

        condition = cursor.last_symbol

        cursor = cursor.parse_one_symbol([
            parser_module.Characters[':']
        ], fail=True).parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, Block)
        body = cursor.last_symbol

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['else'],
            parser_module.Always,
        ])

        if isinstance(cursor.last_symbol, parser_module.Always):
            return cursor.new_from_symbol(cls(
                cursor=cursor,
                condition=condition,
                body=body,
            ))

        cursor = cursor.parse_one_symbol([
            parser_module.Characters[':'],
            If,
        ], fail=True)

        if isinstance(cursor.last_symbol, If):
            return cursor.new_from_symbol(cls(
                cursor=cursor,
                condition=condition,
                body=body,
                else_body=Block([
                    cursor.last_symbol
                ]),
            ))

        cursor = cursor.parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, Block)
        return cursor.new_from_symbol(cls(
            cursor=cursor,
            condition=condition,
            body=body,
            else_body=cursor.last_symbol,
        ))

    @property
    def expressions(self):
        yield self.condition

    @property
    def statements(self):
        yield self.body

        if self.else_body is not None:
            yield self.else_body


@attr.s(frozen=True, slots=True)
class For(Statement):
    """Represents a for loop. Iterates over all the items in ``iterable``, executing the
    statements in ``body`` for each item. If there are no more items in ``iterable``,
    ``else_body`` is executed (if provided). (If the loop body executes a ``Break`` statement,
    the ``else_body`` is not executed.)
    """
    iterable: expression_module.Expression = attr.ib()
    receiver: expression_module.LValue = attr.ib()
    body: Block = attr.ib()
    else_body: typing.Optional[Block] = attr.ib(default=None)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['for']
        ])

        cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
            parser_module.Characters['in']
        ], fail=True)

        assert isinstance(cursor.last_symbol, expression_module.Expression)
        receiver = expression_module.LValue.from_expression(cursor.last_symbol)

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['in']
        ], fail=True)

        cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
            parser_module.Characters[':']
        ], fail=True)

        iterable = cursor.last_symbol

        cursor = cursor.parse_one_symbol([
            parser_module.Characters[':']
        ], fail=True).parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, Block)
        body = cursor.last_symbol

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['else'],
            parser_module.Always,
        ])

        if isinstance(cursor.last_symbol, parser_module.Always):
            return cursor.new_from_symbol(cls(
                cursor=cursor,
                receiver=receiver,
                iterable=iterable,
                body=body,
            ))

        cursor = cursor.parse_one_symbol([
            parser_module.Characters[':'],
            If,
        ], fail=True)

        if isinstance(cursor.last_symbol, If):
            return cursor.new_from_symbol(cls(
                cursor=cursor,
                receiver=receiver,
                iterable=iterable,
                body=body,
                else_body=Block([
                    cursor.last_symbol
                ]),
            ))

        cursor = cursor.parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, Block)
        return cursor.new_from_symbol(cls(
            cursor=cursor,
            receiver=receiver,
            iterable=iterable,
            body=body,
            else_body=cursor.last_symbol,
        ))

    @property
    def expressions(self):
        yield self.iterable
        yield self.receiver

    @property
    def receivers(self):
        yield self.receiver

    @property
    def statements(self):
        yield self.body

        if self.else_body is not None:
            yield self.else_body


@attr.s(frozen=True, slots=True)
class Break(Statement):
    """Break out of the current loop.
    """
    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['break']
        ]).parse_one_symbol([
            parser_module.EndLine
        ], fail=True)

        return cursor.new_from_symbol(cls(
            cursor=cursor
        ))


@attr.s(frozen=True, slots=True)
class Continue(Statement):
    """Skip the rest of the loop body and begin the next iteration.
    """
    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['continue']
        ]).parse_one_symbol([
            parser_module.EndLine
        ], fail=True)

        return cursor.new_from_symbol(cls(
            cursor=cursor
        ))


@attr.s(frozen=True, slots=True)
class With(Statement):
    """Use a context manager. A context manager usually wraps a resource; upon
    leaving the ``With`` block, the context manager is closed.

    Optionally, the context manager may produce a value upon being opened; this value
    is assigned to ``receiver`` (if provided).
    """
    context_manager: expression_module.Expression = attr.ib()
    body: Block = attr.ib()
    receiver: typing.Optional[expression_module.LValue] = attr.ib(default=None)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['with']
        ])

        context_managers = []

        while True:
            cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.Characters['as'],
                parser_module.Characters[':'],
                parser_module.Characters[','],
            ], fail=True)

            context_manager = cursor.last_symbol
            receiver = None

            cursor = cursor.parse_one_symbol([
                parser_module.Characters['as'],
                parser_module.Characters[':'],
                parser_module.Characters[','],
            ], fail=True)

            if isinstance(cursor.last_symbol, parser_module.Characters['as']):
                cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
                    parser_module.Characters[':'],
                    parser_module.Characters[','],
                ], fail=True)

                assert isinstance(cursor.last_symbol, expression_module.Expression)
                receiver = expression_module.LValue.from_expression(cursor.last_symbol)

                cursor = cursor.parse_one_symbol([
                    parser_module.Characters[':'],
                    parser_module.Characters[','],
                ], fail=True)

            context_managers.append((context_manager, receiver))

            if isinstance(cursor.last_symbol, parser_module.Characters[':']):
                break

        cursor = cursor.parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, Block)
        body = cursor.last_symbol

        def nest_context_managers(i):
            nonlocal body
            context_manager_, receiver_ = context_managers[i]
            if i < len(context_managers) - 1:
                inner_body = Block([
                    nest_context_managers(i + 1)
                ])
            else:
                inner_body = body
            return cls(
                cursor=cursor,
                context_manager=context_manager_,
                receiver=receiver_,
                body=inner_body,
            )

        return cursor.new_from_symbol(nest_context_managers(0))

    @property
    def receivers(self):
        if self.receiver is not None:
            yield self.receiver

    @property
    def expressions(self):
        yield self.context_manager

        if self.receiver is not None:
            yield self.receiver

    @property
    def statements(self):
        yield self.body


@attr.s(frozen=True, slots=True)
class Try(Statement):
    """Define exception handlers or cleanup code for a block.

    When an exception is thrown from ``body``, the exception handlers are checked
    in order. The first handler which catches the exception is executed. The handler
    may optionally re-raise the exception, and if no handler catches the exception,
    then the exception is re-raised.

    If no exception is thrown from ``body``, ``else_body`` is executed (if provided).

    In all cases, ``finally_body`` is executed after all other blocks. If ``finally_body``
    contains a ``Return`` statement, this implicitly catches the exception. If
    ``finally_body`` throws an exception, this exception is added to the stack trace.
    """
    @attr.s(frozen=True, slots=True)
    class ExceptionHandler:
        exception: expression_module.Expression = attr.ib()
        body: Block = attr.ib()
        receiver: typing.Optional[expression_module.LValue] = attr.ib(default=None)

    body: Block = attr.ib()
    exception_handlers: typing.Sequence[ExceptionHandler] = attr.ib(factory=tuple, converter=tuple)
    else_body: typing.Optional[Block] = attr.ib(default=None)
    finally_body: typing.Optional[Block] = attr.ib(default=None)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['try']
        ]).parse_one_symbol([
            parser_module.Characters[':']
        ], fail=True).parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, Block)
        body = cursor.last_symbol
        exception_handlers: list[Try.ExceptionHandler] = []
        else_body = None
        finally_body = None

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['except'],
            parser_module.Characters['else'],
            parser_module.Characters['finally'],
        ], fail=True)

        while isinstance(cursor.last_symbol, parser_module.Characters['except']):
            cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.Characters['as'],
                parser_module.Characters[':'],
            ], fail=True)

            assert isinstance(cursor.last_symbol, expression_module.Expression)
            exception: expression_module.Expression = cursor.last_symbol
            receiver = None

            cursor = cursor.parse_one_symbol([
                parser_module.Characters['as'],
                parser_module.Characters[':'],
            ], fail=True)

            if isinstance(cursor.last_symbol, parser_module.Characters['as']):
                cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
                    parser_module.Characters[':'],
                ], fail=True)

                assert isinstance(cursor.last_symbol, expression_module.Expression)
                receiver = expression_module.LValue.from_expression(cursor.last_symbol)

                cursor = cursor.parse_one_symbol([
                    parser_module.Characters[':'],
                ], fail=True)

            cursor = cursor.parse_one_symbol([
                parser_module.EndLine
            ], fail=True)

            cursor = cursor.parse_one_symbol([
                Block
            ], fail=True)
            assert isinstance(cursor.last_symbol, Block)

            exception_handlers.append(Try.ExceptionHandler(
                exception=exception,
                body=cursor.last_symbol,
                receiver=receiver,
            ))

            cursor = cursor.parse_one_symbol([
                parser_module.Characters['except'],
                parser_module.Characters['else'],
                parser_module.Characters['finally'],
                parser_module.Always,
            ])

        if isinstance(cursor.last_symbol, parser_module.Characters['else']):
            cursor = cursor.parse_one_symbol([
                parser_module.Characters[':']
            ], fail=True).parse_one_symbol([
                parser_module.EndLine
            ], fail=True).parse_one_symbol([
                Block
            ], fail=True)

            assert isinstance(cursor.last_symbol, Block)
            else_body = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.Characters['finally'],
                parser_module.Always,
            ])

        if isinstance(cursor.last_symbol, parser_module.Characters['finally']):
            cursor = cursor.parse_one_symbol([
                parser_module.Characters[':']
            ], fail=True).parse_one_symbol([
                parser_module.EndLine
            ], fail=True).parse_one_symbol([
                Block
            ], fail=True)

            assert isinstance(cursor.last_symbol, Block)
            finally_body = cursor.last_symbol

        return cursor.new_from_symbol(cls(
            cursor=cursor,
            body=body,
            exception_handlers=exception_handlers,
            else_body=else_body,
            finally_body=finally_body,
        ))

    @property
    def receivers(self):
        for exception_handler in self.exception_handlers:
            if exception_handler.receiver is not None:
                yield exception_handler.receiver

    @property
    def expressions(self):
        for exception_handler in self.exception_handlers:
            yield exception_handler.exception

            if exception_handler.receiver is not None:
                yield exception_handler.receiver

    @property
    def statements(self):
        yield self.body

        for exception_handler in self.exception_handlers:
            yield exception_handler.body

        if self.else_body is not None:
            yield self.else_body

        if self.finally_body is not None:
            yield self.finally_body


@attr.s(frozen=True, slots=True)
class Raise(Statement):
    expression: typing.Optional[expression_module.Expression] = attr.ib(default=None)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['raise'],
        ]).parse_one_symbol([
            parser_module.EndLine,
            parser_module.Always,
        ])

        expression = None

        if isinstance(cursor.last_symbol, parser_module.Always):
            cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.EndLine
            ], fail=True)

            assert isinstance(cursor.last_symbol, expression_module.Expression)
            expression = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.EndLine
            ], fail=True)

        return cursor.new_from_symbol(cls(
            cursor=cursor,
            expression=expression,
        ))

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class Return(Statement):
    expression: typing.Optional[expression_module.Expression] = attr.ib(default=None)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['return'],
        ]).parse_one_symbol([
            parser_module.EndLine,
            parser_module.Always,
        ])

        expression = None

        if isinstance(cursor.last_symbol, parser_module.Always):
            cursor = expression_module.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.EndLine
            ], fail=True)

            assert isinstance(cursor.last_symbol, expression_module.Expression)
            expression = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.EndLine
            ], fail=True)

        return cursor.new_from_symbol(cls(
            cursor=cursor,
            expression=expression,
        ))

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class Nonlocal(Statement):
    variables: typing.Sequence[expression_module.Variable] = attr.ib(factory=tuple, converter=tuple)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['nonlocal']
        ]).parse_one_symbol([
            expression_module.Variable
        ], fail=True)

        variables: list[expression_module.Variable] = []
        while True:
            assert isinstance(cursor.last_symbol, expression_module.Variable)
            variables.append(cursor.last_symbol)

            cursor = cursor.parse_one_symbol([
                parser_module.Characters[','],
                parser_module.EndLine,
            ], fail=True)

            if isinstance(cursor.last_symbol, parser_module.EndLine):
                break

            cursor = cursor.parse_one_symbol([
                expression_module.Variable
            ], fail=True)

        return cursor.new_from_symbol(cls(
            variables=variables
        ))

    @property
    def expressions(self):
        yield from self.variables
