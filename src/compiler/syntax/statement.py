from __future__ import annotations

import abc
import typing

import attr

from . import expression as expression_module


@attr.s(frozen=True, slots=True)
class Statement(metaclass=abc.ABCMeta):
    """A statement represents some action to be carried out.
    """
    def linearize(self) -> typing.Generator[Statement, None, None]:
        """Iterate over all descendant statements of this statement in an order
        consistent with the order of execution.
        """
        yield from []


@attr.s(frozen=True, slots=True)
class ReceiverStatement(metaclass=abc.ABCMeta):
    """A ReceiverStatement is a statement which assigns to an LValue.
    """
    @property
    @abc.abstractmethod
    def receivers(self) -> list[expression_module.LValue]:
        pass


@attr.s(frozen=True, slots=True)
class Block(Statement):
    statements: typing.Sequence[Statement] = attr.ib(converter=tuple)

    def linearize(self):
        for statement in self.statements:
            yield from statement.linearize()
            yield statement


@attr.s(frozen=True, slots=True)
class Assignment(ReceiverStatement):
    _receivers: typing.Sequence[expression_module.LValue] = attr.ib(converter=tuple)
    expression: expression_module.Expression = attr.ib()

    @property
    def receivers(self):
        return list(self._receivers)


@attr.s(frozen=True, slots=True)
class Expression(Statement):
    expression: expression_module.Expression = attr.ib()


@attr.s(frozen=True, slots=True)
class If(Statement):
    condition: expression_module.Expression = attr.ib()
    body: Block = attr.ib()
    else_body: typing.Optional[Block] = attr.ib(default=None)

    def linearize(self):
        yield from self.body.linearize()
        yield self.body

        if self.else_body is not None:
            yield from self.else_body.linearize()
            yield self.else_body


@attr.s(frozen=True, slots=True)
class While(Statement):
    condition: expression_module.Expression = attr.ib()
    body: Block = attr.ib()
    else_body: typing.Optional[Block] = attr.ib(default=None)

    def linearize(self):
        yield from self.body.linearize()
        yield self.body

        if self.else_body is not None:
            yield from self.else_body.linearize()
            yield self.else_body


@attr.s(frozen=True, slots=True)
class For(ReceiverStatement):
    iterable: expression_module.Expression = attr.ib()
    receiver: expression_module.LValue = attr.ib()
    body: Block = attr.ib()
    else_body: typing.Optional[Block] = attr.ib(default=None)
    is_async: bool = attr.ib(default=False)

    def linearize(self):
        yield from self.body.linearize()
        yield self.body

        if self.else_body is not None:
            yield from self.else_body.linearize()
            yield self.else_body

    @property
    def receivers(self):
        return [self.receiver]


@attr.s(frozen=True, slots=True)
class Break(Statement):
    pass


@attr.s(frozen=True, slots=True)
class Continue(Statement):
    pass


@attr.s(frozen=True, slots=True)
class With(ReceiverStatement):
    context_manager: expression_module.Expression = attr.ib()
    body: Block = attr.ib()
    receiver: typing.Optional[expression_module.LValue] = attr.ib(default=None)
    is_async: bool = attr.ib(default=False)

    def linearize(self):
        yield from self.body.linearize()
        yield self.body

    @property
    def receivers(self):
        if self.receiver is not None:
            return [self.receiver]
        return []


@attr.s(frozen=True, slots=True)
class Try(ReceiverStatement):
    @attr.s(frozen=True, slots=True)
    class ExceptionHandler:
        exception: expression_module.Expression = attr.ib()
        receiver: typing.Optional[expression_module.LValue] = attr.ib()
        body: Block = attr.ib()

    body: Block = attr.ib()
    exception_handlers: typing.Sequence[ExceptionHandler] = attr.ib(factory=tuple, converter=tuple)
    else_body: typing.Optional[Block] = attr.ib(default=None)
    finally_body: typing.Optional[Block] = attr.ib(default=None)

    def linearize(self):
        yield from self.body.linearize()
        yield self.body

        for exception_handler in self.exception_handlers:
            yield from exception_handler.body.linearize()
            yield exception_handler.body

        if self.else_body is not None:
            yield from self.else_body.linearize()
            yield self.else_body

        if self.finally_body is not None:
            yield from self.finally_body.linearize()
            yield self.finally_body

    @property
    def receivers(self):
        return [
            exception_handler.receiver
            for exception_handler in self.exception_handlers
        ]


@attr.s(frozen=True, slots=True)
class Return(Statement):
    expression: typing.Optional[expression_module.Expression] = attr.ib(default=None)


@attr.s(frozen=True, slots=True)
class Nonlocal(Statement):
    variables: typing.Sequence[expression_module.Variable] = attr.ib(factory=tuple, converter=tuple)
