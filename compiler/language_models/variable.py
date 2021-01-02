import typing

import attr

from . import declarable


@attr.s(frozen=True, slots=True)
class Variable(declarable.Declarable):
    """A Variable is a register in a namespace which can hold runtime values.

    NB: variable.Variable should not be confused with expression.Variable, which
    represents an expression which evaluates to the value of a variable in a scope.
    """
    @attr.s(frozen=True, slots=True)
    class Annotation:
        pass

    annotations: typing.Sequence[Annotation] = attr.ib(converter=tuple, default=(), repr=False)
