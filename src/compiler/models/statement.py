import typing

import attr

from . import expression as expression_module


@attr.s(frozen=True, slots=True)
class Statement:
    pass


@attr.s(frozen=True, slots=True)
class Block:
    statements: typing.Sequence[Statement] = attr.ib(converter=tuple)


@attr.s(frozen=True, slots=True)
class Assignment(Statement):
    receivers: typing.Sequence[expression_module.LValue] = attr.ib(converter=tuple)
    expression: expression_module.Expression


@attr.s(frozen=True, slots=True)
class Expression(Statement):
    expression: expression_module.Expression


@attr.s(frozen=True, slots=True)
class If(Statement):
    condition: expression_module.Expression
    body: Block
    else_body: typing.Optional[Block]


@attr.s(frozen=True, slots=True)
class While(Statement):
    condition: expression_module.Expression
    body: Block
    else_body: typing.Optional[Block]


@attr.s(frozen=True, slots=True)
class For(Statement):
    iterable: expression_module.Expression
    receiver: expression_module.LValue
    body: Block
    else_body: typing.Optional[Block]


@attr.s(frozen=True, slots=True)
class Break(Statement):
    pass


@attr.s(frozen=True, slots=True)
class Continue(Statement):
    pass


@attr.s(frozen=True, slots=True)
class With(Statement):
    context_manager: expression_module.Expression
    receiver: typing.Optional[expression_module.LValue]
    body: Block


@attr.s(frozen=True, slots=True)
class Try(Statement):
    @attr.s(frozen=True, slots=True)
    class ExceptionHandler:
        exception: expression_module.Expression
        receiver: typing.Optional[expression_module.LValue]
        body: Block

    body: Block
    exception_handlers: typing.Sequence[ExceptionHandler] = attr.ib(converter=tuple)
    else_body: typing.Optional[Block]
    finally_body: typing.Optional[Block]


@attr.s(frozen=True, slots=True)
class Return(Statement):
    expression: typing.Optional[expression_module.Expression] = attr.ib(default=None)
