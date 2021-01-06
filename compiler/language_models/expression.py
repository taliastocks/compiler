from __future__ import annotations

import abc
import typing

import attr

from . import declarable
from .. import parser as parser_module


@attr.s(frozen=True, slots=True)
class Expression(parser_module.Symbol, metaclass=abc.ABCMeta):
    """An Expression is a syntactic entity that may be evaluated to determine
    its value.
    """
    @classmethod
    def parse(cls, parser):
        """Parse an expression, taking into account precedence rules,
        into the appropriate subclass.
        """
        # placeholder to allow Variable tests to pass
        return Variable.parse(parser)

    @property
    def expressions(self) -> typing.Iterable[Expression]:
        """Get all the expressions which this expression directly depends on,
        not including descendants of those expressions.
        """
        yield from []

    @property
    def has_yield(self) -> bool:
        """True if this expression yields, otherwise False
        """
        if isinstance(self, (Yield, YieldFrom)):
            return True

        for expression in self.expressions:
            if expression.has_yield:
                return True

        return False


@attr.s(frozen=True, slots=True)
class LValue(Expression, metaclass=abc.ABCMeta):
    """An LValue is an expression which can be assigned to, i.e. it can appear
    on the left-hand side of an `=` sign (thus "L" as in "Left").
    """


@attr.s(frozen=True, slots=True)
class Variable(declarable.Declarable, LValue):
    """A Variable is a register in a namespace which can hold runtime values.

    When used as an expression, evaluates to the value of the variable.
    """
    @attr.s(frozen=True, slots=True)
    class Annotation(parser_module.Symbol, metaclass=abc.ABCMeta):
        pass

    annotations: typing.Sequence[Annotation] = attr.ib(converter=tuple, default=(), repr=False)
    initializer: typing.Optional[Expression] = attr.ib(default=None, repr=False)

    @classmethod
    def parse(cls,
              parser,
              allowed_annotations: typing.Sequence[typing.Type[Variable.Annotation]] = (),
              parse_initializer=False):
        # pylint: disable=unused-argument, arguments-differ
        parser = parser.parse([
            parser_module.Identifier,
        ])
        if isinstance(parser.last_symbol, parser_module.Identifier):
            name = parser.last_symbol.identifier
        else:
            raise RuntimeError('this should be unreachable')

        annotations = []  # noqa
        if allowed_annotations:
            parser = parser.parse([
                parser_module.Characters[':'],
                parser_module.Always,
            ])

            if not isinstance(parser.last_symbol, parser_module.Always):
                while not isinstance(parser.last_symbol, parser_module.Always):
                    parser = parser.parse([*allowed_annotations, parser_module.Always])
                    if isinstance(parser.last_symbol, Variable.Annotation):
                        annotations.append(parser.last_symbol)

                if not annotations:
                    raise parser_module.ParseError(
                        message='expected annotations',
                        parser=parser,
                    )

        initializer = None
        if parse_initializer:
            parser = parser.parse([
                parser_module.Characters['='],
                parser_module.Always,
            ])

            if not isinstance(parser.last_symbol, parser_module.Always):
                parser = parser.parse([
                    Expression,
                    parser_module.Always,
                ])

                if isinstance(parser.last_symbol, Expression):
                    initializer = parser.last_symbol
                else:
                    raise parser_module.ParseError(
                        message='expected initializer expression',
                        parser=parser,
                    )

        return parser.new_from_symbol(cls(
            name=name,
            annotations=annotations,
            initializer=initializer,
        ))


@attr.s(frozen=True, slots=True)
class Unpack(LValue):
    """On assignment, unpack an iterable into a collection of LValues.
    """
    lvalues: typing.Sequence[LValue] = attr.ib(converter=tuple)

    @classmethod
    def parse(cls, parser):
        pass

    @property
    def expressions(self):
        yield from self.lvalues

    @property
    def variable_assignments(self) -> typing.Iterable[Variable]:
        """Iterate over all the variables which unpacking would assign to.
        """
        for lvalue in self.lvalues:
            if isinstance(lvalue, Variable):
                yield lvalue
            elif isinstance(lvalue, Unpack):
                yield from lvalue.variable_assignments


@attr.s(frozen=True, slots=True)
class Subscript(LValue):
    """An array subscript, i.e. ``my_array[3]``.
    """
    operand: Expression = attr.ib()
    subscript: Expression = attr.ib()

    @classmethod
    def parse(cls, parser):
        pass

    @property
    def expressions(self):
        yield self.operand
        yield self.subscript


@attr.s(frozen=True, slots=True)
class Dot(LValue):
    """The dot operator, i.e. ``my_instance.my_member``.
    """
    operand: Expression = attr.ib()
    member: str = attr.ib()

    @classmethod
    def parse(cls, parser):
        pass

    @property
    def expressions(self):
        yield self.operand


@attr.s(frozen=True, slots=True)
class Yield(Expression):
    """Yield a single value from a generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)

    @classmethod
    def parse(cls, parser):
        pass

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class YieldFrom(Expression):
    """Yield all the values of an iterable. This can only be used from within
    a generator.

        is_async: Await each promise in the iterable before yielding it. This
            option can only be used from within an async generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)
    is_async: bool = attr.ib(default=False)

    @classmethod
    def parse(cls, parser):
        pass

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class Await(Expression):
    """Await a promise. This can only be used from within an async function
    or async generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)

    @classmethod
    def parse(cls, parser):
        pass

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class IfElse(Expression):
    """Choose between expressions to evaluate.
    """
    condition: Expression = attr.ib()
    value: Expression = attr.ib()
    else_value: Expression = attr.ib()

    @classmethod
    def parse(cls, parser):
        pass

    @property
    def expressions(self):
        yield self.condition
        yield self.value
        yield self.else_value


@attr.s(frozen=True, slots=True)
class Comprehension(Expression):
    """Define a generator in terms of another iterable.
    """

    @attr.s(frozen=True, slots=True)
    class Loop:
        iterable: Expression = attr.ib()
        receiver: LValue = attr.ib()

    value: Expression = attr.ib()
    loops: typing.Sequence[Loop] = attr.ib(converter=tuple)
    condition: typing.Optional[Expression] = attr.ib(default=None)

    @classmethod
    def parse(cls, parser):
        pass

    @property
    def expressions(self):
        for loop in self.loops:
            yield loop.iterable
            yield loop.receiver

        yield self.value

        if self.condition is not None:
            yield self.condition
