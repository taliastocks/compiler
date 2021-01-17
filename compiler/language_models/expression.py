from __future__ import annotations

import abc
import typing

import attr
import immutabledict

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
        cursor = cursor.parse_one_symbol([
            parser_module.Identifier,
        ])
        if isinstance(cursor.last_symbol, parser_module.Identifier):
            name = cursor.last_symbol.identifier
        else:
            raise RuntimeError('this should be unreachable')

        annotations = []  # noqa
        if allowed_annotations:
            cursor = cursor.parse_one_symbol([
                parser_module.Characters[':'],
                parser_module.Always,
            ])

            if not isinstance(cursor.last_symbol, parser_module.Always):
                while not isinstance(cursor.last_symbol, parser_module.Always):
                    cursor = cursor.parse_one_symbol([*allowed_annotations, parser_module.Always])
                    if isinstance(cursor.last_symbol, Variable.Annotation):
                        annotations.append(cursor.last_symbol)
                        cursor = cursor.parse_one_symbol([
                            parser_module.Characters[','],
                            parser_module.Always,
                        ])

                if not annotations:
                    raise parser_module.ParseError(
                        message='expected annotations',
                        cursor=cursor,
                    )

        initializer = None
        if parse_initializer:
            cursor = cursor.parse_one_symbol([
                parser_module.Characters['='],
                parser_module.Always,
            ])

            if not isinstance(cursor.last_symbol, parser_module.Always):
                cursor = ExpressionParser.parse(
                    cursor=cursor,
                    allow_comma=False,
                    allow_newline=False,
                ) or cursor

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

    @abc.abstractmethod
    def new_from_operand_stack(self, cursor: parser_module.Cursor, operands: typing.MutableSequence) -> Operator:
        pass


@attr.s(frozen=True, slots=True)
class UnaryOperator(Operator, metaclass=abc.ABCMeta):
    """An operator which takes exactly one argument.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)

    token: typing.Type[parser_module.Token] = None  # override in subclass

    @classmethod
    def parse(cls, cursor):
        return cursor.parse_one_symbol([
            cls.token
        ]).new_from_symbol(cls())

    @property
    def expressions(self):
        if self.expression:
            yield self.expression

    def new_from_operand_stack(self, cursor, operands):
        if not operands:
            raise parser_module.ParseError('not enough operands', cursor)

        return type(self)(expression=operands.pop())  # noqa


@attr.s(frozen=True, slots=True)
class BinaryOperator(Operator, metaclass=abc.ABCMeta):
    """An operator which takes exactly one argument.
    """
    left: typing.Optional[Expression] = attr.ib(default=None)
    right: typing.Optional[Expression] = attr.ib(default=None)

    token: typing.Type[parser_module.Token] = None  # override in subclass

    @classmethod
    def parse(cls, cursor):
        return cursor.parse_one_symbol([
            cls.token
        ]).new_from_symbol(cls())

    @property
    def expressions(self):
        if self.left is not None:
            yield self.left
        if self.right is not None:
            yield self.right

    def new_from_operand_stack(self, cursor, operands):
        if len(operands) < 2:
            raise parser_module.ParseError('not enough operands', cursor)

        # Instantiate left and right in reverse order because we're popping from a stack.
        return type(self)(right=operands.pop(), left=operands.pop())  # noqa


@attr.s(frozen=True, slots=True)
class Call(Operator):
    """A function call, i.e. ``foo(...args...)``.
    """
    callable: typing.Optional[Expression] = attr.ib(default=None)
    expression_arguments: typing.Sequence[Expression] = attr.ib(converter=tuple, default=())
    keyword_arguments: typing.Mapping[str, Expression] = attr.ib(converter=immutabledict.immutabledict,
                                                                 default=immutabledict.immutabledict())

    begin_token = parser_module.Characters['(']
    end_token = parser_module.Characters[')']

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            cls.begin_token
        ])
        expression_arguments: list[Expression] = []
        keyword_arguments: dict[str, Expression] = {}

        while not isinstance(cursor.last_symbol, cls.end_token):
            # First try to parse the optional keyword name.
            keyword_name: typing.Optional[str] = None
            maybe_keyword_cursor = cursor.parse_one_symbol([
                parser_module.Identifier,
                parser_module.Always,
            ])
            if isinstance(maybe_keyword_cursor.last_symbol, parser_module.Identifier):
                maybe_keyword_name = maybe_keyword_cursor.last_symbol.identifier
                maybe_keyword_cursor = maybe_keyword_cursor.parse_one_symbol([
                    parser_module.Characters['='],
                    parser_module.Always,
                ])
                if isinstance(maybe_keyword_cursor.last_symbol, parser_module.Characters['=']):
                    cursor = maybe_keyword_cursor  # Consume the identifier and "=".
                    keyword_name = maybe_keyword_name

            # Parse the argument value.
            cursor = ExpressionParser.parse(
                cursor=cursor,
                allow_comma=False,
            ) or cursor

            if isinstance(cursor.last_symbol, Expression):
                if keyword_name is not None:
                    keyword_arguments[keyword_name] = cursor.last_symbol
                else:
                    expression_arguments.append(cursor.last_symbol)
            else:
                raise parser_module.ParseError(
                    message='expected expression',
                    cursor=cursor,
                )

            cursor = cursor.parse_one_symbol([
                parser_module.Characters[','],
                cls.end_token,
            ])
            if isinstance(cursor.last_symbol, parser_module.Characters[',']):
                # Allow for a trailing comma in the argument list.
                cursor = cursor.parse_one_symbol([
                    cls.end_token,
                    parser_module.Always,
                ])

        return cursor.new_from_symbol(cls(
            expression_arguments=expression_arguments,
            keyword_arguments=keyword_arguments,
        ))

    @property
    def expressions(self):
        if self.callable is not None:
            yield self.callable
        for argument in self.expression_arguments:
            yield argument
        for argument in self.keyword_arguments.values():
            yield argument

    def new_from_operand_stack(self, cursor, operands):
        if len(operands) < 1:
            raise parser_module.ParseError('not enough operands', cursor)

        return Call(
            callable=operands.pop(),
            expression_arguments=self.expression_arguments,
            keyword_arguments=self.keyword_arguments,
        )


@attr.s(frozen=True, slots=True)
class Dot(Operator, LValue):
    """The dot operator, i.e. ``my_instance.my_member``.
    """
    object: typing.Optional[Expression] = attr.ib(default=None)
    member_name: typing.Optional[str] = attr.ib(default=None)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['.']
        ]).parse_one_symbol([
            parser_module.Identifier
        ])

        if isinstance(cursor.last_symbol, parser_module.Identifier):
            return cursor.new_from_symbol(cls(
                member_name=cursor.last_symbol.identifier
            ))

        raise RuntimeError('this should be unreachable')

    @property
    def expressions(self):
        if self.object is not None:
            yield self.object

    def new_from_operand_stack(self, cursor, operands):
        if len(operands) < 1:
            raise parser_module.ParseError('not enough operands', cursor)

        return Dot(
            object=operands.pop(),
            member_name=self.member_name,
        )


@attr.s(frozen=True, slots=True)
class Subscript(Call, LValue):
    """An array subscript, i.e. ``my_array[3]``.
    """
    subscriptable: typing.Optional[Expression] = attr.ib(default=None)
    expression_arguments: typing.Sequence[Expression] = attr.ib(converter=tuple, default=())
    keyword_arguments: typing.Mapping[str, Expression] = attr.ib(converter=immutabledict.immutabledict,
                                                                 default=immutabledict.immutabledict())

    begin_token = parser_module.Characters['[']
    end_token = parser_module.Characters[']']

    @property
    def expressions(self):
        if self.subscriptable is not None:
            yield self.subscriptable
        for argument in self.expression_arguments:
            yield argument
        for argument in self.keyword_arguments.values():
            yield argument

    def new_from_operand_stack(self, cursor, operands):
        if len(operands) < 1:
            raise parser_module.ParseError('not enough operands', cursor)

        return Subscript(
            subscriptable=operands.pop(),
            expression_arguments=self.expression_arguments,
            keyword_arguments=self.keyword_arguments,
        )


@attr.s(frozen=True, slots=True)
class Await(UnaryOperator):
    """Await a promise. This can only be used from within an async function
    or async generator.
    """
    higher_precedence_operators = Call.higher_precedence_operators | {Call, Dot, Subscript}

    token = parser_module.Characters['await']


@attr.s(frozen=True, slots=True)
class Exponentiation(BinaryOperator):
    """a ** b
    """
    higher_precedence_operators = Await.higher_precedence_operators | {Await}

    token = parser_module.Characters['**']

    @classmethod
    def precedes_on_right(cls, other: typing.Type[Operator]) -> bool:
        if other is cls:
            return True
        return super().precedes_on_right(other)


@attr.s(frozen=True, slots=True)
class Positive(UnaryOperator):
    """+expr
    """
    higher_precedence_operators = Exponentiation.higher_precedence_operators | {Exponentiation}

    token = parser_module.Characters['+']


@attr.s(frozen=True, slots=True)
class Negative(UnaryOperator):
    """-expr
    """
    higher_precedence_operators = Positive.higher_precedence_operators

    token = parser_module.Characters['-']


@attr.s(frozen=True, slots=True)
class BitInverse(UnaryOperator):
    """~expr
    """
    higher_precedence_operators = Positive.higher_precedence_operators

    token = parser_module.Characters['~']


@attr.s(frozen=True, slots=True)
class Multiply(BinaryOperator):
    """a * b
    """
    higher_precedence_operators = Positive.higher_precedence_operators | {Positive, Negative, BitInverse}

    token = parser_module.Characters['*']


@attr.s(frozen=True, slots=True)
class MatrixMultiply(BinaryOperator):
    """a @ b
    """
    higher_precedence_operators = Multiply.higher_precedence_operators

    token = parser_module.Characters['@']


@attr.s(frozen=True, slots=True)
class FloorDivide(BinaryOperator):
    """a // b
    """
    higher_precedence_operators = Multiply.higher_precedence_operators

    token = parser_module.Characters['//']


@attr.s(frozen=True, slots=True)
class Divide(BinaryOperator):
    """a / b
    """
    higher_precedence_operators = Multiply.higher_precedence_operators

    token = parser_module.Characters['/']


@attr.s(frozen=True, slots=True)
class Modulo(BinaryOperator):
    """a % b
    """
    higher_precedence_operators = Multiply.higher_precedence_operators

    token = parser_module.Characters['%']


@attr.s(frozen=True, slots=True)
class Add(BinaryOperator):
    """a + b
    """
    higher_precedence_operators = Multiply.higher_precedence_operators | {
        Multiply, MatrixMultiply, Divide, FloorDivide, Modulo}

    token = parser_module.Characters['+']


@attr.s(frozen=True, slots=True)
class Subtract(BinaryOperator):
    """a - b
    """
    higher_precedence_operators = Add.higher_precedence_operators

    token = parser_module.Characters['-']


@attr.s(frozen=True, slots=True)
class ShiftLeft(BinaryOperator):
    """a << b
    """
    higher_precedence_operators = Add.higher_precedence_operators | {Add, Subtract}

    token = parser_module.Characters['<<']


@attr.s(frozen=True, slots=True)
class ShiftRight(BinaryOperator):
    """a >> b
    """
    higher_precedence_operators = ShiftLeft.higher_precedence_operators

    token = parser_module.Characters['>>']


@attr.s(frozen=True, slots=True)
class BitAnd(BinaryOperator):
    """a & b
    """
    higher_precedence_operators = ShiftLeft.higher_precedence_operators | {ShiftLeft, ShiftRight}

    token = parser_module.Characters['&']


@attr.s(frozen=True, slots=True)
class BitXor(BinaryOperator):
    """a ^ b
    """
    higher_precedence_operators = BitAnd.higher_precedence_operators | {BitAnd}

    token = parser_module.Characters['^']


@attr.s(frozen=True, slots=True)
class BitOr(BinaryOperator):
    """a | b
    """
    higher_precedence_operators = BitXor.higher_precedence_operators | {BitXor}

    token = parser_module.Characters['|']


@attr.s(frozen=True, slots=True)
class In(BinaryOperator):
    """a in b
    """
    higher_precedence_operators = BitOr.higher_precedence_operators | {BitOr}

    token = parser_module.Characters['in']


@attr.s(frozen=True, slots=True)
class NotIn(BinaryOperator):
    """a not in b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Regex['not +in']


@attr.s(frozen=True, slots=True)
class IsNot(BinaryOperator):
    """a is not b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Regex['is +not']


@attr.s(frozen=True, slots=True)
class Is(BinaryOperator):
    """a is b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Characters['is']


@attr.s(frozen=True, slots=True)
class LessThanOrEqual(BinaryOperator):
    """a <= b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Characters['<=']


@attr.s(frozen=True, slots=True)
class LessThan(BinaryOperator):
    """a < b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Characters['<']


@attr.s(frozen=True, slots=True)
class GreaterThanOrEqual(BinaryOperator):
    """a >= b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Characters['>=']


@attr.s(frozen=True, slots=True)
class GreaterThan(BinaryOperator):
    """a > b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Characters['>']


@attr.s(frozen=True, slots=True)
class NotEqual(BinaryOperator):
    """a != b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Characters['!=']


@attr.s(frozen=True, slots=True)
class Equal(BinaryOperator):
    """a == b
    """
    higher_precedence_operators = In.higher_precedence_operators

    token = parser_module.Characters['==']


@attr.s(frozen=True, slots=True)
class Not(UnaryOperator):
    """not expr
    """
    higher_precedence_operators = In.higher_precedence_operators | {
        In, NotIn, Is, IsNot, LessThan, LessThanOrEqual, GreaterThan, GreaterThanOrEqual, NotEqual, Equal}

    token = parser_module.Characters['not']


@attr.s(frozen=True, slots=True)
class And(BinaryOperator):
    """a and b
    """
    higher_precedence_operators = Not.higher_precedence_operators | {Not}

    token = parser_module.Characters['and']


@attr.s(frozen=True, slots=True)
class Or(BinaryOperator):
    """a or b
    """
    higher_precedence_operators = And.higher_precedence_operators | {And}

    token = parser_module.Characters['or']


@attr.s(frozen=True, slots=True)
class IfElse(Operator):
    """Choose between expressions to evaluate.
    """
    condition: Expression = attr.ib()
    true_value: typing.Optional[Expression] = attr.ib(default=None)
    false_value: typing.Optional[Expression] = attr.ib(default=None)

    higher_precedence_operators = Or.higher_precedence_operators | {Or}

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['if']
        ])
        cursor = ExpressionParser.parse(cursor) or cursor

        if isinstance(cursor.last_symbol, Expression):
            condition = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.Characters['else']
            ])

            return cursor.new_from_symbol(cls(
                condition=condition
            ))

        raise parser_module.ParseError(
            message='expected expression',
            cursor=cursor,
        )

    def new_from_operand_stack(self, cursor, operands):
        if len(operands) < 2:
            raise parser_module.ParseError('not enough operands', cursor)

        # Instantiate false_value and true_value in reverse order because we're popping from a stack.
        return IfElse(condition=self.condition, false_value=operands.pop(), true_value=operands.pop())

    @property
    def expressions(self):
        yield self.condition
        if self.true_value is not None:
            yield self.true_value
        if self.false_value is not None:
            yield self.false_value


@attr.s(frozen=True, slots=True)
class Lambda(UnaryOperator):
    """Inline function definition.
    """
    higher_precedence_operators = IfElse.higher_precedence_operators | {IfElse}

    token = parser_module.Characters['lambda:']  # TODO: arguments; this is oversimplified


@attr.s(frozen=True, slots=True)
class Assignment(BinaryOperator):
    """a := b
    """
    higher_precedence_operators = Lambda.higher_precedence_operators | {Lambda}

    token = parser_module.Characters[':=']

    @property
    def variable_assignments(self):
        # https://github.com/python-attrs/attrs/issues/652
        yield from super(Assignment, self).variable_assignments  # pylint: disable=super-with-arguments

        if isinstance(self.left, Variable):
            yield self.left


@attr.s(frozen=True, slots=True)
class YieldFrom(UnaryOperator):
    """Yield all the values of an iterable. This can only be used from within
    a generator.

        is_async: Await each promise in the iterable before yielding it. This
            option can only be used from within an async generator.
    """
    is_async: bool = attr.ib(default=False)

    higher_precedence_operators = Assignment.higher_precedence_operators | {Assignment}

    token = parser_module.Regex['(async +)?yield +from']

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            cls.token
        ])
        return cursor.new_from_symbol(cls(
            is_async=cursor.last_symbol.groups[1] is not None  # noqa
        ))

    def new_from_operand_stack(self, cursor, operands):
        if not operands:
            raise parser_module.ParseError('not enough operands', cursor)

        return type(self)(expression=operands.pop(), is_async=self.is_async)  # noqa


@attr.s(frozen=True, slots=True)
class Yield(UnaryOperator):
    """Yield a single value from a generator.
    """
    higher_precedence_operators = YieldFrom.higher_precedence_operators

    token = parser_module.Characters['yield']


@attr.s(frozen=True, slots=True)
class StarStar(UnaryOperator):
    """**mapping
    """
    higher_precedence_operators = Yield.higher_precedence_operators | {YieldFrom, Yield}

    token = parser_module.Characters['**']


@attr.s(frozen=True, slots=True)
class Star(UnaryOperator):
    """*iterable
    """
    higher_precedence_operators = StarStar.higher_precedence_operators

    token = parser_module.Characters['*']


@attr.s(frozen=True, slots=True)
class Slice(BinaryOperator):
    """a:b
    """
    higher_precedence_operators = StarStar.higher_precedence_operators | {StarStar, Star}

    token = parser_module.Characters[':']


@attr.s(frozen=True, slots=True)
class Comma(BinaryOperator):
    """a, b
    """
    higher_precedence_operators = Slice.higher_precedence_operators | {Slice}

    token = parser_module.Characters[',']


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
        parser_module.Always,
    )
    prefix_operators: typing.Sequence[typing.Type[UnaryOperator]] = (
        Await, Positive, Negative, BitInverse, Not, Lambda, YieldFrom, Yield, StarStar, Star,
        parser_module.Always,
    )
    infix_operators: typing.Sequence[typing.Type[Operator]] = (
        Exponentiation, Multiply, MatrixMultiply, FloorDivide, Divide, Modulo, Add, Subtract,
        ShiftLeft, ShiftRight, BitAnd, BitXor, BitOr, In, NotIn, IsNot, Is,
        LessThanOrEqual, LessThan, GreaterThanOrEqual, GreaterThan,
        NotEqual, Equal, And, Or, IfElse, Assignment, Slice, Comma,
        parser_module.Always,
    )
    immediate_operators: typing.Sequence[typing.Type[Operator]] = (
        Call, Dot, Subscript,
        parser_module.Always,
    )

    @classmethod
    def parse(cls, cursor,  # pylint: disable=arguments-differ
              allow_comma: bool = True,
              allow_slice: bool = True,
              allow_newline: bool = True):
        """Parse an expression according to the rules of operator precedence.

        :param cursor:
        :param allow_comma: whether or not the comma operator is allowed in this context
        :param allow_slice: whether or not the slice operator is allowed in this context
        :param allow_newline: whether or not a newline is allowed to follow an operand in this context
            (newlines are always allowed to follow operators, as this is unambiguous)
        """
        # pylint: disable=too-many-branches; todo: factor out some of this logic
        operators: list[Operator] = []
        operands: list[Expression] = []

        while True:
            # Consume all the leading prefix operators.
            cursor = cls._consume_prefix_operators(cursor, operators)

            # Consume an operand.
            new_cursor = cls._consume_operand(cursor, operands)
            if new_cursor is None:  # No operand could be matched.
                if operators or operands:
                    raise parser_module.ParseError('expected an operand', cursor)
                return None
            cursor = new_cursor

            # Consume all the immediate operators.
            cursor = cls._consume_immediate_operators(cursor, operators, operands, allow_newline)

            # Consume an infix operator.
            new_cursor = cls._consume_infix_operator(
                cursor,
                operators,
                operands,
                allow_comma,
                allow_slice,
                allow_newline,
            )
            if new_cursor is not None:
                cursor = new_cursor
            else:
                # End the expression.
                break

        # Evaluate all remaining operators on the stack.
        while operators:
            operands.append(operators.pop().new_from_operand_stack(cursor, operands))

        # There should be exactly one operand left if all went well.
        if len(operands) > 1:
            raise parser_module.ParseError('too many operands', cursor)
        if not operands:
            raise parser_module.ParseError('no operands', cursor)

        return cursor.new_from_symbol(operands[-1])

    @classmethod
    def _consume_prefix_operators(cls, cursor, operators):
        while True:
            cursor = cursor.parse_one_symbol(cls.prefix_operators)
            if isinstance(cursor.last_symbol, Operator):
                operators.append(cursor.last_symbol)
            else:
                return cursor

    @classmethod
    def _consume_infix_operator(cls,  # pylint: disable=too-many-arguments
                                cursor,
                                operators,
                                operands,
                                allow_comma,
                                allow_slice,
                                allow_newline):
        if cls._newline_ends_expression(cursor, allow_newline):
            # If newlines aren't allowed, they can't precede an infix operator.
            return None

        new_cursor = cursor.parse_one_symbol(cls.infix_operators)

        if not allow_comma and isinstance(new_cursor.last_symbol, Comma):
            # End the expression at the first comma operator if allow_comma=False.
            return None
        if not allow_slice and isinstance(new_cursor.last_symbol, Slice):
            # End the expression at the first slice operator if allow_slice=False.
            return None

        if isinstance(new_cursor.last_symbol, Operator):
            # Evaluate all the operators in the stack which bind more tightly.
            while operators and not new_cursor.last_symbol.precedes_on_right(type(operators[-1])):
                operands.append(operators.pop().new_from_operand_stack(cursor, operands))

            # Consume the operator.
            operators.append(new_cursor.last_symbol)
            return new_cursor

        # End the expression.
        return None

    @classmethod
    def _consume_immediate_operators(cls, cursor, operators, operands, allow_newline):
        while True:
            if cls._newline_ends_expression(cursor, allow_newline):
                # If newlines aren't allowed, they can't precede an immediate operator.
                return cursor

            new_cursor = cursor.parse_one_symbol(cls.immediate_operators)

            if isinstance(new_cursor.last_symbol, Operator):
                # Evaluate all the operators in the stack which bind more tightly.
                while operators and not new_cursor.last_symbol.precedes_on_right(type(operators[-1])):
                    operands.append(operators.pop().new_from_operand_stack(cursor, operands))

                # Consume the operator.
                operators.append(new_cursor.last_symbol)
                cursor = new_cursor
            else:
                return new_cursor

    @classmethod
    def _consume_operand(cls, cursor, operands):
        cursor = cursor.parse_one_symbol(cls.operands)
        if isinstance(cursor.last_symbol, Expression):
            operands.append(cursor.last_symbol)
            return cursor
        return None

    @staticmethod
    def _newline_ends_expression(cursor, allow_newlines):
        if not allow_newlines:
            # End the expression at the first newline if allow_newline=False.
            new_cursor = cursor.parse_one_symbol([parser_module.EndLine, parser_module.Always])
            if isinstance(new_cursor.last_symbol, parser_module.EndLine):
                return True
        return False
