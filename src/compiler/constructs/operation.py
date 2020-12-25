import typing

import attr

from . import value


@attr.s(frozen=True, slots=True)
class Operation:
    pass


@attr.s(frozen=True, slots=True)
class Sequence(Operation):
    operations: typing.Sequence[Operation] = attr.ib(factory=tuple, converter=tuple)


@attr.s(frozen=True, slots=True)
class Conditional(Operation):
    condition: value.Value
    consequence: Operation
    alternative: Operation
