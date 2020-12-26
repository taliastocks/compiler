import abc
import typing

import attr


@attr.s(frozen=True, slots=True)
class Expression(metaclass=abc.ABCMeta):
    """An Expression is a syntactic entity that may be evaluated to determine
    its value.
    """


@attr.s(frozen=True, slots=True)
class LValue(Expression):
    """An LValue is an expression which can be assigned to, i.e. it can appear
    on the left-hand side of an `=` sign (thus "L" as in "Left").
    """


@attr.s(frozen=True, slots=True)
class Variable(LValue):
    """A Variable is an expression which evaluates to the value of a
    variable in a scope.

    NB: expression.Variable should not be confused with variable.Variable, which
    represents a register in a namespace which can hold runtime values.

        name: The name of the variable.
    """
    name: str


@attr.s(frozen=True, slots=True)
class Subscript(LValue):
    """An array subscript, i.e. ``my_array[3]``.
    """
    operand: Expression
    subscript: Expression


@attr.s(frozen=True, slots=True)
class Dot(LValue):
    """The dot operator, i.e. ``my_instance.my_member``.
    """
    operand: Expression
    member: str


@attr.s(frozen=True, slots=True)
class Yield(Expression):
    """Yield a single value from a generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)


@attr.s(frozen=True, slots=True)
class YieldFrom(Expression):
    """Yield all the values of an iterable. This can only be used from within
    a generator.

        is_async: Await each promise in the iterable before yielding it. This
            option can only be used from within an async generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)
    is_async: bool = attr.ib(default=False)


@attr.s(frozen=True, slots=True)
class Await(Expression):
    """Await a promise. This can only be used from within an async function
    or async generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)


@attr.s(frozen=True, slots=True)
class IfElse(Expression):
    """Choose between expressions to evaluate.
    """
    condition: Expression
    value: Expression
    else_value: Expression


@attr.s(frozen=True, slots=True)
class Comprehension(Expression):
    """Define a generator in terms of another iterable.
    """

    @attr.s(frozen=True, slots=True)
    class Loop:
        iterable: Expression
        receiver: LValue

    value: Expression
    loops: typing.Sequence[Loop] = attr.ib(converter=tuple)
    condition: typing.Optional[Expression] = attr.ib(default=None)
