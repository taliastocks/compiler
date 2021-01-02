from __future__ import annotations

import abc
import typing

import attr

from . import expression as expression_module


@attr.s(frozen=True, slots=True)
class Statement(metaclass=abc.ABCMeta):
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
            if isinstance(lvalue, expression_module.Unpack):
                yield from lvalue.variable_assignments

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


@attr.s(frozen=True, slots=True)
class Block(Statement):
    """A sequence of statements to be executed in order.
    """
    statements: typing.Sequence[Statement] = attr.ib(converter=tuple, factory=list)


@attr.s(frozen=True, slots=True)
class Assignment(Statement):
    """An assignment statement, e.g. ``foo = 3`` or ``foo = bar = 42``.
    """
    receivers: typing.Sequence[expression_module.LValue] = attr.ib(converter=tuple)
    expression: expression_module.Expression = attr.ib()

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
    is_async: bool = attr.ib(default=False)

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


@attr.s(frozen=True, slots=True)
class Continue(Statement):
    """Skip the rest of the loop body and begin the next iteration.
    """


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
    is_async: bool = attr.ib(default=False)

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

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class Return(Statement):
    expression: typing.Optional[expression_module.Expression] = attr.ib(default=None)

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class Nonlocal(Statement):
    variables: typing.Sequence[expression_module.Variable] = attr.ib(factory=tuple, converter=tuple)
