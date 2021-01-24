from __future__ import annotations

import abc
import typing

import attr
import immutabledict

from . import declarable
from .. import parser as parser_module

# pylint: disable=fixme
# pylint: disable=too-many-lines


@attr.s
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


@attr.s
class Literal(Expression, metaclass=abc.ABCMeta):
    """A literal value.
    """


@attr.s(frozen=True, slots=True)
class Number(Literal):
    """Represents a number. Can represent integers and floating point values without rounding.
    """
    digits_part: int = attr.ib(default=0)
    magnitude_part: int = attr.ib(default=0)

    @classmethod
    def parse(cls, cursor):
        regex_class = parser_module.Regex[r'(\d[\d\']*)(?:\.(\d[\d\']*))?(?:[eE]([-+])?(\d[\d\']*))?']
        cursor: regex_class = cursor.parse_one_symbol([
            regex_class
        ])
        if not isinstance(cursor.last_symbol, regex_class):
            raise RuntimeError('this should be unreachable')

        whole_part, fraction_part, magnitude_sign, magnitude_part = cursor.last_symbol.groups[1:]  # noqa

        # Remove any place markers.
        whole_part = whole_part.replace("'", '')
        fraction_part = (fraction_part or '').replace("'", '').rstrip('0')
        magnitude_part = (magnitude_part or '0').replace("'", '')

        digits_part = int(whole_part)

        if magnitude_part:
            magnitude_part = int(magnitude_part)
        else:
            magnitude_part = 0

        if magnitude_sign == '-':
            magnitude_part *= -1

        if fraction_part:
            magnitude_part -= len(fraction_part)
            digits_part *= pow(10, len(fraction_part))
            digits_part += int(fraction_part)

        return cursor.new_from_symbol(cls(
            digits_part=digits_part,
            magnitude_part=magnitude_part,
            cursor=cursor,
        ))


@attr.s
class LValue(Expression, metaclass=abc.ABCMeta):
    """An LValue is an expression which can be assigned to, i.e. it can appear
    on the left-hand side of an `=` sign (thus "L" as in "Left").
    """
    @staticmethod
    def from_expression(expression: Expression) -> LValue:
        """Convert an expression into an LValue if possible.
        """
        if isinstance(expression, LValue):
            return expression

        if isinstance(expression, Comma):
            return Unpack([
                LValue.from_expression(expr)
                for expr in expression.to_expression_list()
            ], cursor=expression.cursor)

        if isinstance(expression, Parenthesized):
            inner_expression = expression.expression

            if isinstance(inner_expression, Comma):
                # Comma expansion will wrap this in an Unpack for us.
                return LValue.from_expression(inner_expression)

            # If there's only one value, wrap it in Unpack.
            return Unpack(
                [LValue.from_expression(inner_expression)],
                cursor=inner_expression.cursor,
            )

        raise parser_module.ParseError('expected LValue expression', expression.cursor)


@attr.s(frozen=True, slots=True)
class Variable(declarable.Declarable, LValue):
    """A Variable is a register in a namespace which can hold runtime values.

    When used as an expression, evaluates to the value of the variable.
    """
    @attr.s
    class Annotation(metaclass=abc.ABCMeta):
        pass

    annotation: typing.Optional[typing.Union[Expression, Annotation]] = attr.ib(default=None, repr=False)
    initializer: typing.Optional[Expression] = attr.ib(default=None, repr=False)

    @classmethod
    def parse(cls,
              cursor,
              parse_annotation: bool = False,
              parse_initializer: bool = False,
              allow_comma_in_annotations: bool = False):
        # pylint: disable=arguments-differ
        cursor = cursor.parse_one_symbol([
            parser_module.Identifier,
            parser_module.Always,
        ])
        if isinstance(cursor.last_symbol, parser_module.Identifier):
            name = cursor.last_symbol.identifier
        else:
            return None

        annotation = None
        if parse_annotation:
            cursor = cursor.parse_one_symbol([
                parser_module.Characters[':'],
                parser_module.Always,
            ])

            if isinstance(cursor.last_symbol, parser_module.Characters[':']):
                cursor = ExpressionParser.parse(
                    cursor,
                    stop_symbols=[
                        parser_module.Characters[':'],
                        parser_module.EndLine,
                    ] + (
                        [] if allow_comma_in_annotations else
                        [parser_module.Characters[',']]
                    ),
                )

                if isinstance(cursor.last_symbol, Expression):
                    annotation = cursor.last_symbol
                else:
                    raise parser_module.ParseError(
                        message='expected variable annotation',
                        cursor=cursor,
                    )

        initializer = None
        if parse_initializer:
            cursor = cursor.parse_one_symbol([
                parser_module.Characters['='],
                parser_module.Always,
            ])

            if isinstance(cursor.last_symbol, parser_module.Characters['=']):
                cursor = ExpressionParser.parse(
                    cursor=cursor,
                    stop_symbols=[
                        parser_module.Characters[','],
                        parser_module.Characters[':'],
                        parser_module.EndLine,
                    ],
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
            annotation=annotation,
            initializer=initializer,
            cursor=cursor,
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
class Parenthesized(Expression):
    """Define a parenthesized expression.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)

    begin_token = parser_module.Characters['(']
    end_token = parser_module.Characters[')']

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            cls.begin_token
        ])
        cursor = ExpressionParser.parse(cursor) or cursor

        if isinstance(cursor.last_symbol, Expression):
            expression = cursor.last_symbol
        else:
            expression = None

        cursor = cursor.parse_one_symbol([
            cls.end_token
        ])

        return cursor.new_from_symbol(cls(
            expression=expression,
            cursor=cursor,
        ))

    @property
    def expressions(self):
        if self.expression is not None:
            yield self.expression


@attr.s(frozen=True, slots=True)
class DictionaryOrSet(Parenthesized):
    """Define a dictionary or set literal or comprehension.
    """
    begin_token = parser_module.Characters['{']
    end_token = parser_module.Characters['}']


@attr.s(frozen=True, slots=True)
class List(Parenthesized):
    """Define a list literal or comprehension.
    """
    begin_token = parser_module.Characters['[']
    end_token = parser_module.Characters[']']


@attr.s(kw_only=True)  # https://youtrack.jetbrains.com/issue/PY-46406
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


@attr.s
class UnaryOperator(Operator, metaclass=abc.ABCMeta):
    """An operator which takes exactly one argument.
    """
    expression: typing.Optional[Expression] = attr.ib(default=None)

    token: typing.Type[parser_module.Token] = None  # override in subclass

    @classmethod
    def parse(cls, cursor):
        return cursor.parse_one_symbol([
            cls.token
        ]).new_from_symbol(cls(cursor=cursor))

    @property
    def expressions(self):
        if self.expression:
            yield self.expression

    def new_from_operand_stack(self, cursor, operands):
        if not operands:
            raise parser_module.ParseError('not enough operands', cursor)

        return type(self)(expression=operands.pop(), cursor=cursor)  # noqa


@attr.s
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
        ]).new_from_symbol(cls(cursor=cursor))

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
        return type(self)(right=operands.pop(), left=operands.pop(), cursor=cursor)  # noqa


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
                stop_symbols=[parser_module.Characters[',']],
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
            cursor=cursor,
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
            cursor=cursor,
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
                member_name=cursor.last_symbol.identifier,
                cursor=cursor,
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
            cursor=cursor,
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
            cursor=cursor,
        )


@attr.s(frozen=True, slots=True)
class Await(UnaryOperator):
    """Await a promise.
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
                condition=condition,
                cursor=cursor,
            ))

        raise parser_module.ParseError(
            message='expected expression',
            cursor=cursor,
        )

    def new_from_operand_stack(self, cursor, operands):
        if len(operands) < 2:
            raise parser_module.ParseError('not enough operands', cursor)

        # Instantiate false_value and true_value in reverse order because we're popping from a stack.
        return IfElse(
            condition=self.condition,
            false_value=operands.pop(),
            true_value=operands.pop(),
            cursor=cursor,
        )

    @property
    def expressions(self):
        yield self.condition
        if self.true_value is not None:
            yield self.true_value
        if self.false_value is not None:
            yield self.false_value


@attr.s(frozen=True, slots=True)
class Lambda(Operator):
    """Inline function definition.
    """
    arguments: ArgumentList = attr.ib(factory=lambda: ArgumentList())
    expression: typing.Optional[Expression] = attr.ib(default=None)

    higher_precedence_operators = IfElse.higher_precedence_operators | {IfElse}

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            parser_module.Characters['lambda']
        ])

        # We can't have annotations in a Lambda because annotations are
        # denoted by ":", which also denotes the body of the Lambda.
        cursor = ArgumentList.parse(cursor, parse_annotations=False)

        if not isinstance(cursor.last_symbol, ArgumentList):
            raise RuntimeError('this should be unreachable')

        arguments = cursor.last_symbol

        return cursor.parse_one_symbol([
            parser_module.Characters[':']
        ], fail=True).new_from_symbol(cls(
            arguments=arguments,
            cursor=cursor,
        ))

    def new_from_operand_stack(self, cursor, operands):
        if len(operands) < 1:
            raise parser_module.ParseError('not enough operands', cursor)

        return Lambda(
            arguments=self.arguments,
            expression=operands.pop(),
            cursor=cursor,
        )

    @property
    def expressions(self):
        if self.expression:
            yield self.expression


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
    """
    higher_precedence_operators = Assignment.higher_precedence_operators | {Assignment}
    token = parser_module.Regex['yield +from']

    def new_from_operand_stack(self, cursor, operands):
        if not operands:
            raise parser_module.ParseError('not enough operands', cursor)

        return YieldFrom(
            expression=operands.pop(),
            cursor=cursor,
        )


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
class Colon(BinaryOperator):
    """a:b
    """
    higher_precedence_operators = StarStar.higher_precedence_operators | {StarStar, Star}
    token = parser_module.Characters[':']


@attr.s(frozen=True, slots=True)
class Comprehension(Operator):
    """Define a generator in terms of another iterable.
    """

    @attr.s(frozen=True, slots=True)
    class Loop:
        receiver: LValue = attr.ib()
        iterable: typing.Optional[Expression] = attr.ib(default=None)

    value: typing.Optional[Expression] = attr.ib(default=None)
    loops: typing.Sequence[Loop] = attr.ib(converter=tuple, default=())
    condition: typing.Optional[Expression] = attr.ib(default=None)

    higher_precedence_operators = Colon.higher_precedence_operators | {Colon}

    @classmethod
    def parse(cls, cursor):
        loops: list[Comprehension.Loop] = []

        while True:
            cursor = cursor.parse_one_symbol([
                parser_module.Characters['for']
            ])

            cursor = ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.Characters['in']
            ], fail=True)

            if not isinstance(cursor.last_symbol, Expression):
                raise RuntimeError('this should be unreachable')

            receiver: LValue = LValue.from_expression(cursor.last_symbol)

            cursor = cursor.parse_one_symbol([
                parser_module.Characters['in']
            ], fail=True)

            iterable_cursor = ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.Characters['for'],
                parser_module.Characters['if'],
                parser_module.Characters[','],
            ])

            next_cursor = iterable_cursor.parse_one_symbol([
                parser_module.Characters['for'],
                parser_module.Characters['if'],
                parser_module.Always,
            ])

            if isinstance(next_cursor.last_symbol, parser_module.Characters['for']):
                # We need to parse another loop after this one.
                cursor = iterable_cursor
                loops.append(Comprehension.Loop(
                    receiver=receiver,
                    iterable=iterable_cursor.last_symbol,
                ))
                continue

            if isinstance(next_cursor.last_symbol, parser_module.Characters['if']):
                # We're done parsing loops. The next expression will be the condition.
                cursor = next_cursor
                loops.append(Comprehension.Loop(
                    receiver=receiver,
                    iterable=iterable_cursor.last_symbol,
                ))
            else:
                # We were done parsing loops at "in". The next expression will be final loop iterable.
                loops.append(Comprehension.Loop(
                    receiver=receiver,
                ))
            break

        return cursor.new_from_symbol(cls(
            loops=loops,
            cursor=cursor,
        ))

    def new_from_operand_stack(self, cursor, operands):
        if len(operands) < 2:
            raise parser_module.ParseError('not enough operands', cursor)
        if len(self.loops) < 1:
            raise RuntimeError('this should be unreachable')

        # Instantiate value and iterable/condition in reverse order because we're popping from a stack.
        iterable_or_condition = operands.pop()
        value = operands.pop()

        if self.loops[-1].iterable is None:
            # The second operand is the final loop iterable.
            return Comprehension(
                value=value,
                loops=[
                    *self.loops[:-1],
                    Comprehension.Loop(
                        receiver=self.loops[-1].receiver,
                        iterable=iterable_or_condition,
                    ),
                ],
                cursor=cursor,
            )

        # Otherwise, the second operand is the loop condition.
        return Comprehension(
            value=value,
            loops=self.loops,
            condition=iterable_or_condition,
            cursor=cursor,
        )

    @property
    def expressions(self):
        for loop in self.loops:
            yield loop.iterable
            yield loop.receiver

        if self.value is not None:
            yield self.value

        if self.condition is not None:
            yield self.condition


@attr.s(frozen=True, slots=True)
class Comma(BinaryOperator):
    """a, b
    """
    higher_precedence_operators = Comprehension.higher_precedence_operators | {Comprehension}
    token = parser_module.Characters[',']

    def to_expression_list(self) -> typing.Iterable[Expression]:
        """Expand chained Comma operators into an expression list.
        """
        if isinstance(self.left, Comma):
            yield from self.left.to_expression_list()
        else:
            yield self.left

        if isinstance(self.right, Comma):
            yield from self.right.to_expression_list()
        else:
            yield self.right


@attr.s(frozen=True, slots=True)
class ExpressionParser(parser_module.Parser):
    """Parse an expression according to the rules of operator precedence.
    """
    operands: typing.Sequence[typing.Type[Expression]] = (
        Number,
        Variable,
        Parenthesized,
        DictionaryOrSet,
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
        NotEqual, Equal, And, Or, IfElse, Assignment, Colon, Comprehension, Comma,
        parser_module.Always,
    )
    immediate_operators: typing.Sequence[typing.Type[Operator]] = (
        Call, Dot, Subscript,
        parser_module.Always,
    )

    @classmethod
    def parse(cls, cursor,  # pylint: disable=arguments-differ
              stop_symbols: typing.Sequence[parser_module.Symbol] = (),
              fail: bool = False):
        """Parse an expression according to the rules of operator precedence.

        Never throws parser_module.NoMatchError.

        :param cursor:
        :param stop_symbols: stop parsing the expression when one of these symbols appears
            after an operand has been parsed
        :param fail: throw parser_module.ParseError if no expression is found
        """
        operators: list[Operator] = []
        operands: list[Expression] = []

        while True:
            # Consume all the leading prefix operators.
            cursor = cls._consume_prefix_operators(cursor, operators)

            # Consume an operand.
            new_cursor = cls._consume_operand(cursor, operands)
            if new_cursor is None:  # No operand could be matched.
                if operators and isinstance(operators[-1], Comma):
                    # Don't worry about a trailing comma, but it ends the expression.
                    operators.pop()
                    break
                if operators or operands or fail:
                    raise parser_module.ParseError('expected an operand', cursor)
                return None
            cursor = new_cursor

            # Detect stop symbols.
            try:
                cursor.parse_one_symbol(stop_symbols)
            except parser_module.NoMatchError:
                pass  # We can continue parsing this expression.
            else:
                # End the expression.
                break

            # Consume all the immediate operators.
            cursor = cls._consume_immediate_operators(cursor, operators, operands)

            # Consume an infix operator.
            new_cursor = cls._consume_infix_operator(
                cursor,
                operators,
                operands,
            )
            if new_cursor is not None:
                cursor = new_cursor
            else:
                # End the expression.
                break

        # Evaluate all remaining operators on the stack.
        while operators:
            operand = operators.pop().new_from_operand_stack(cursor, operands)
            if operand.cursor is None:
                raise RuntimeError('this should be unreachable')
            operands.append(operand)

        # There should be exactly one operand left if all went well.
        if len(operands) != 1:
            raise RuntimeError('this should be unreachable')

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
                                operands):
        cursor = cursor.parse_one_symbol(cls.infix_operators)

        if isinstance(cursor.last_symbol, Operator):
            # Evaluate all the operators in the stack which bind more tightly.
            while operators and not cursor.last_symbol.precedes_on_right(type(operators[-1])):
                operands.append(operators.pop().new_from_operand_stack(cursor, operands))

            # Consume the operator.
            operators.append(cursor.last_symbol)
            return cursor

        # End the expression.
        return None

    @classmethod
    def _consume_immediate_operators(cls, cursor, operators, operands):
        while True:
            cursor = cursor.parse_one_symbol(cls.immediate_operators)

            if isinstance(cursor.last_symbol, Operator):
                # Evaluate all the operators in the stack which bind more tightly.
                while operators and not cursor.last_symbol.precedes_on_right(type(operators[-1])):
                    operands.append(operators.pop().new_from_operand_stack(cursor, operands))

                # Consume the operator.
                operators.append(cursor.last_symbol)
            else:
                return cursor

    @classmethod
    def _consume_operand(cls, cursor, operands):
        cursor = cursor.parse_one_symbol(cls.operands)
        if isinstance(cursor.last_symbol, Expression):
            operands.append(cursor.last_symbol)
            return cursor
        return None


@attr.s(frozen=True, slots=True)
class ArgumentList(parser_module.Symbol):
    """A list of function arguments.

    Why is this here? This isn't an Expression!

        Although ArgumentList is not an expression, it participates in a dependency
        cycle with Lambda and Variable. Since Python makes module dependency cycles
        difficult, this goes here for now. When the compiler is rewritten in Sibilance,
        this class and Argument should both move to a new module.
    """
    arguments: typing.Sequence[Argument] = attr.ib(converter=tuple, default=())

    @classmethod
    def parse(cls, cursor, parse_annotations: bool = True):
        # pylint: disable=too-many-branches, arguments-differ
        arguments: list[Argument] = []
        saw_end_position_only_marker = False
        saw_begin_keyword_only_marker = False
        saw_extra_positionals = False
        saw_extra_keywords = False

        while True:
            cursor = cursor.parse_one_symbol([
                parser_module.Characters['**'],
                parser_module.Characters['*'],
                parser_module.Characters['/'],
                parser_module.Always,
            ])

            new_cursor = Variable.parse(
                cursor=cursor,
                parse_annotation=parse_annotations,
                parse_initializer=True,
            )

            if isinstance(cursor.last_symbol, parser_module.Characters['*']):
                if new_cursor is not None and isinstance(new_cursor.last_symbol, Variable):
                    # This is "extra positional args" (which also acts as a keyword-only marker).
                    if saw_extra_positionals:
                        raise parser_module.ParseError('multiple "extra positional" arguments found', cursor)
                    saw_extra_positionals = True

                    arguments.append(Argument(
                        variable=new_cursor.last_symbol,
                        is_positional=True,
                        is_extra=True,
                    ))
                    cursor = new_cursor

                if saw_begin_keyword_only_marker:
                    raise parser_module.ParseError('multiple "begin keyword-only" markers found', cursor)
                saw_begin_keyword_only_marker = True

            elif isinstance(cursor.last_symbol, parser_module.Characters['**']):
                if new_cursor is None or not isinstance(new_cursor.last_symbol, Variable):
                    raise parser_module.ParseError('expected Variable', cursor)
                if saw_extra_keywords:
                    raise parser_module.ParseError('multiple "extra keyword" arguments found', cursor)
                saw_extra_keywords = True

                arguments.append(Argument(
                    variable=new_cursor.last_symbol,
                    is_keyword=True,
                    is_extra=True,
                ))
                cursor = new_cursor

            elif isinstance(cursor.last_symbol, parser_module.Characters['/']):
                if saw_end_position_only_marker:
                    raise parser_module.ParseError('multiple "end position-only" markers found', cursor)
                if saw_begin_keyword_only_marker:
                    raise parser_module.ParseError(
                        '"end position-only" marker found after "begin keyword-only" marker',
                        cursor,
                    )
                saw_end_position_only_marker = True

                # Rewrite all the previous arguments to position-only.
                for i, argument in enumerate(arguments):
                    if argument.is_extra:
                        continue  # Don't rewrite "extra" arguments.
                    arguments[i] = Argument(
                        variable=argument.variable,
                        is_positional=True,
                        is_keyword=False,
                        is_extra=False,
                    )

            elif new_cursor and isinstance(new_cursor.last_symbol, Variable):
                arguments.append(Argument(
                    variable=new_cursor.last_symbol,
                    is_positional=not saw_begin_keyword_only_marker,
                    is_keyword=True,
                    is_extra=False,
                ))
                cursor = new_cursor

            else:
                break  # No more arguments to parse.

            cursor = cursor.parse_one_symbol([
                parser_module.Characters[','],
                parser_module.Always,
            ])

            if isinstance(cursor.last_symbol, parser_module.Always):
                break  # Additional arguments can only follow a comma, so we're done.

        return cursor.new_from_symbol(cls(
            arguments=arguments,
            cursor=cursor,
        ))


@attr.s(frozen=True, slots=True)
class Argument:
    """A function argument.
    """
    variable: Variable = attr.ib()
    is_positional: bool = attr.ib(default=False)
    is_keyword: bool = attr.ib(default=False)
    is_extra: bool = attr.ib(default=False)
