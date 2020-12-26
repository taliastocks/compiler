import typing

import attr


@attr.s(frozen=True, slots=True)
class Expression:
    pass


@attr.s(frozen=True, slots=True)
class LValue(Expression):
    pass


@attr.s(frozen=True, slots=True)
class Variable(LValue):
    name: str


@attr.s(frozen=True, slots=True)
class Subscript(LValue):
    operand: Expression
    subscript: Expression


@attr.s(frozen=True, slots=True)
class Dot(LValue):
    operand: Expression
    member: str


@attr.s(frozen=True, slots=True)
class Yield(Expression):
    expression: typing.Optional[Expression] = attr.ib(default=None)


@attr.s(frozen=True, slots=True)
class YieldFrom(Expression):
    expression: typing.Optional[Expression] = attr.ib(default=None)


@attr.s(frozen=True, slots=True)
class Await(Expression):
    expression: typing.Optional[Expression] = attr.ib(default=None)
