from __future__ import annotations

import abc
import typing

import attr

from . import declarable
from .. import parser as parser_module

# pylint: disable=fixme
# pylint: disable=too-many-lines


@attr.s(frozen=True, slots=True)
class Expression(parser_module.Symbol, metaclass=abc.ABCMeta):
    """An Expression is a syntactic entity that may be evaluated to determine
    its value.
    """
    @property
    def expressions(self) -> typing.Iterable[Expression]:
        """Get all the expressions which this expression directly depends on,
        not including descendants of those expressions.
        """
        yield from []

    @property
    def variable_assignments(self) -> typing.Iterable[Variable]:
        """Get all the variable assignments that result from executing this expression.
        """
        for expression in self.expressions:
            yield from expression.variable_assignments

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
              cursor,
              allowed_annotations: typing.Sequence[typing.Type[Variable.Annotation]] = (),
              parse_initializer=False):
        # pylint: disable=unused-argument, arguments-differ
        cursor = cursor.parse([
            parser_module.Identifier,
        ])
        if isinstance(cursor.last_symbol, parser_module.Identifier):
            name = cursor.last_symbol.identifier
        else:
            raise RuntimeError('this should be unreachable')

        annotations = []  # noqa
        if allowed_annotations:
            cursor = cursor.parse([
                parser_module.Characters[':'],
                parser_module.Always,
            ])

            if not isinstance(cursor.last_symbol, parser_module.Always):
                while not isinstance(cursor.last_symbol, parser_module.Always):
                    cursor = cursor.parse([*allowed_annotations, parser_module.Always])
                    if isinstance(cursor.last_symbol, Variable.Annotation):
                        annotations.append(cursor.last_symbol)

                if not annotations:
                    raise parser_module.ParseError(
                        message='expected annotations',
                        cursor=cursor,
                    )

        initializer = None
        if parse_initializer:
            cursor = cursor.parse([
                parser_module.Characters['='],
                parser_module.Always,
            ])

            if not isinstance(cursor.last_symbol, parser_module.Always):
                cursor = ExpressionParser.parse(cursor) or cursor

                if isinstance(cursor.last_symbol, Expression):
                    initializer = cursor.last_symbol
                else:
                    raise parser_module.ParseError(
                        message='expected initializer expression',
                        cursor=cursor,
                    )

        return cursor.new_from_symbol(cls(
            name=name,
            annotations=annotations,
            initializer=initializer,
        ))


@attr.s(frozen=True, slots=True)
class Unpack(LValue):
    """On assignment, unpack an iterable into a collection of LValues.

    ``Unpack`` should only ever be used as the target of an assignment.
    """
    lvalues: typing.Sequence[LValue] = attr.ib(converter=tuple)

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield from self.lvalues

    @property
    def variable_assignments(self) -> typing.Iterable[Variable]:
        """Iterate over all the variables which unpacking would assign to.
        """
        # https://github.com/python-attrs/attrs/issues/652
        yield from super(Unpack, self).variable_assignments  # pylint: disable=super-with-arguments

        for lvalue in self.lvalues:
            if isinstance(lvalue, Variable):
                yield lvalue


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
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        for loop in self.loops:
            yield loop.iterable
            yield loop.receiver

        yield self.value

        if self.condition is not None:
            yield self.condition


@attr.s(frozen=True, slots=True)
class Parenthesized(Expression):
    """Define a parenthesized expression.
    """
    expression: Expression = attr.ib()

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class Dictionary(Expression):
    """Define a dictionary literal or comprehension.
    """
    expression: Expression = attr.ib()

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class Set(Expression):
    """Define a set literal or comprehension.
    """
    expression: Expression = attr.ib()

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class List(Expression):
    """Define a list literal or comprehension.
    """
    expression: Expression = attr.ib()

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True, kw_only=True)  # https://youtrack.jetbrains.com/issue/PY-46406
class Operator(Expression, metaclass=abc.ABCMeta):
    """An operator is an expression which takes expressions as arguments.

    When parsing operators, some operators have precedence over others.
    """
    higher_precedence_operators: frozenset[typing.Type[Operator]] = frozenset()

    @classmethod
    def precedes_on_right(cls, other: typing.Type[Operator]) -> bool:
        """Returns True if this operator, when appearing to the right of ``other``, binds more tightly.
        """
        return cls in other.higher_precedence_operators


@attr.s(frozen=True, slots=True)
class Call(Operator):
    """A function call, i.e. ``foo(...args...)``.
    """
    function: Expression = attr.ib()
    # TODO: arguments

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.function
        # TODO: get expressions from arguments


@attr.s(frozen=True, slots=True)
class Dot(Operator, LValue):
    """The dot operator, i.e. ``my_instance.my_member``.
    """
    operand: Expression = attr.ib()
    member: str = attr.ib()

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.operand


@attr.s(frozen=True, slots=True)
class Subscript(Operator, LValue):
    """An array subscript, i.e. ``my_array[3]``.
    """
    operand: Expression = attr.ib()
    subscript: Expression = attr.ib()

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.operand
        yield self.subscript


@attr.s(frozen=True, slots=True)
class Await(Operator):
    """Await a promise. This can only be used from within an async function
    or async generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)

    higher_precedence_operators = Call.higher_precedence_operators | {Call, Dot, Subscript}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class Exponentiation(Operator):
    """a ** b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Await.higher_precedence_operators | {Await}

    @classmethod
    def precedes_on_right(cls, other: typing.Type[Operator]) -> bool:
        if other is cls:
            return True
        return super().precedes_on_right(other)

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Positive(Operator):
    """+expr
    """
    expression: Expression = attr.ib()

    higher_precedence_operators = Exponentiation.higher_precedence_operators | {Exponentiation}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class Negative(Operator):
    """-expr
    """
    expression: Expression = attr.ib()

    higher_precedence_operators = Positive.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class BitInverse(Operator):
    """~expr
    """
    expression: Expression = attr.ib()

    higher_precedence_operators = Positive.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class Multiply(Operator):
    """a * b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Positive.higher_precedence_operators | {Positive, Negative, BitInverse}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class MatrixMultiply(Operator):
    """a @ b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Multiply.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Divide(Operator):
    """a / b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Multiply.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class FloorDivide(Operator):
    """a // b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Multiply.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Modulo(Operator):
    """a % b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Multiply.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Add(Operator):
    """a + b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Multiply.higher_precedence_operators | {
        Multiply, MatrixMultiply, Divide, FloorDivide, Modulo}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Subtract(Operator):
    """a - b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Add.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class ShiftLeft(Operator):
    """a << b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Add.higher_precedence_operators | {Add, Subtract}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class ShiftRight(Operator):
    """a >> b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = ShiftLeft.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class BitAnd(Operator):
    """a & b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = ShiftLeft.higher_precedence_operators | {ShiftLeft, ShiftRight}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class BitXor(Operator):
    """a ^ b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = BitAnd.higher_precedence_operators | {BitAnd}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class BitOr(Operator):
    """a | b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = BitXor.higher_precedence_operators | {BitXor}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class In(Operator):
    """a in b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = BitOr.higher_precedence_operators | {BitOr}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class NotIn(Operator):
    """a not in b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Is(Operator):
    """a is b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class IsNot(Operator):
    """a is not b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class LessThan(Operator):
    """a < b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class LessThanOrEqual(Operator):
    """a <= b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class GreaterThan(Operator):
    """a > b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class GreaterThanOrEqual(Operator):
    """a >= b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class NotEqual(Operator):
    """a != b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Equal(Operator):
    """a == b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Not(Operator):
    """not expr
    """
    expression: Expression = attr.ib()

    higher_precedence_operators = In.higher_precedence_operators | {
        In, NotIn, Is, IsNot, LessThan, LessThanOrEqual, GreaterThan, GreaterThanOrEqual, NotEqual, Equal}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class And(Operator):
    """a and b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Not.higher_precedence_operators | {Not}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class Or(Operator):
    """a or b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = And.higher_precedence_operators | {And}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class IfElse(Operator):
    """Choose between expressions to evaluate.
    """
    condition: Expression = attr.ib()
    value: Expression = attr.ib()
    else_value: Expression = attr.ib()

    higher_precedence_operators = Or.higher_precedence_operators | {Or}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.condition
        yield self.value
        yield self.else_value


@attr.s(frozen=True, slots=True)
class Lambda(Operator):
    """Inline function definition.
    """

    higher_precedence_operators = IfElse.higher_precedence_operators | {IfElse}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield from []  # TODO


@attr.s(frozen=True, slots=True)
class Assignment(Operator):
    """a := b
    """
    left: LValue = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Lambda.higher_precedence_operators | {Lambda}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right

    @property
    def variable_assignments(self):
        # https://github.com/python-attrs/attrs/issues/652
        yield from super(Assignment, self).variable_assignments  # pylint: disable=super-with-arguments

        if isinstance(self.left, Variable):
            yield self.left


@attr.s(frozen=True, slots=True)
class Yield(Operator):
    """Yield a single value from a generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)

    higher_precedence_operators = Assignment.higher_precedence_operators | {Assignment}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class YieldFrom(Operator):
    """Yield all the values of an iterable. This can only be used from within
    a generator.

        is_async: Await each promise in the iterable before yielding it. This
            option can only be used from within an async generator.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)
    is_async: bool = attr.ib(default=False)

    higher_precedence_operators = Yield.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class Star(Operator):
    """*iterable
    """
    expression: Expression = attr.ib()

    higher_precedence_operators = Yield.higher_precedence_operators | {Yield, YieldFrom}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class StarStar(Operator):
    """**mapping
    """
    expression: Expression = attr.ib()

    higher_precedence_operators = Star.higher_precedence_operators

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.expression


@attr.s(frozen=True, slots=True)
class Comma(Operator):
    """a, b
    """
    left: Expression = attr.ib()
    right: Expression = attr.ib()

    higher_precedence_operators = Star.higher_precedence_operators | {Star, StarStar}

    @classmethod
    def parse(cls, cursor):
        pass

    @property
    def expressions(self):
        yield self.left
        yield self.right


@attr.s(frozen=True, slots=True)
class ExpressionParser(parser_module.Parser):
    """Parse an expression according to the rules of operator precedence.
    """
    operands: typing.Sequence[typing.Type[Expression]] = (
        Variable,
        Parenthesized,
        Dictionary,
        Set,
        List,
    )

    @classmethod
    def parse(cls, cursor):
        """Parse an expression according to the rules of operator precedence.
        """
        return Variable.parse(cursor)  # placeholder
