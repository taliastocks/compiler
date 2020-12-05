import abc
import typing

import attr

from .. import c
from . import string, types


@attr.s(frozen=True, slots=True)
class Expression(c.ProgramPartBase, metaclass=abc.ABCMeta):
    """Represents an expression.
    """

    @abc.abstractmethod
    def render_expression(self) -> typing.Generator[str, None, None]:
        """Render the expression.
        """
        raise NotImplementedError


@attr.s(frozen=True, slots=True)
class LiteralExpression(Expression, metaclass=abc.ABCMeta):
    """Represents a literal expression.
    """


@attr.s(frozen=True, slots=True)
class IntegerLiteral(LiteralExpression):
    """Represents an integer literal expression.
    """
    value: int = attr.ib(validator=attr.validators.instance_of(int))
    width: int = attr.ib(validator=attr.validators.in_([16, 32, 64]))
    signed: bool = attr.ib(validator=attr.validators.instance_of(bool))

    def render_expression(self):
        yield '{value}{sign_suffix}{width_suffix}'.format(
            value=self.value,
            sign_suffix='' if self.signed else 'u',
            width_suffix={
                16: '',
                32: 'l',
                64: 'll',
            }[self.width]
        )

    @width.default
    def _init_width(self):
        if self.value >> 15 in (-1, 0):
            return 16
        if self.value >> 31 in (-1, 0):
            return 32
        return 64

    @signed.default
    def _init_signed(self):
        return self.value < (1 << (self.width - 1))

    @value.validator
    def _check_value(self, _, value):
        valid = True

        if self.signed:
            if value >> (self.width - 1) not in (-1, 0):
                valid = False
        else:
            if value >> self.width != 0:
                valid = False

        if not valid:
            raise ValueError('value {} out of range (signed={}, width={})'.format(
                value,
                self.signed,
                self.width,
            ))


@attr.s(frozen=True, slots=True)
class BytesLiteral(LiteralExpression):
    """Represents a character literal expression representing raw bytes (not unicode).
    """
    value: bytes = attr.ib(validator=attr.validators.instance_of(bytes))

    chunk_size: int = attr.ib(validator=attr.validators.instance_of(int), default=80)

    def render_expression(self):
        chunks = [self.value[i:i + self.chunk_size] for i in range(0, len(self.value), self.chunk_size)]

        if not chunks:
            yield '""'
        else:
            for i, chunk in enumerate(chunks):
                escaped_chunk = '"{}"'.format(string.escape_bytes(chunk))
                if i == 0:
                    yield escaped_chunk
                else:
                    yield self.indent, escaped_chunk


@attr.s(frozen=True, slots=True)
class LValueExpression(Expression, metaclass=abc.ABCMeta):
    """Represents an expression which can appear on the left side of an assignment operator.
    """


@attr.s(frozen=True, slots=True)
class Variable(LValueExpression):
    """Represents a variable.
    """
    name: str = attr.ib(validator=attr.validators.instance_of(str))

    def render_expression(self):
        yield self.name


@attr.s(frozen=True, slots=True)
class Dot(LValueExpression):
    """Represents member dereference, i.e. ``my_struct.my_member``.
    """
    operand: Expression = attr.ib(validator=attr.validators.instance_of(Expression))
    member: str = attr.ib(validator=attr.validators.instance_of(str))

    def render_expression(self):
        operand_rendering = list(self.operand.render_expression())

        for i, line in enumerate(operand_rendering):
            if i == len(operand_rendering) - 1:
                yield line, '.', self.member
            else:
                yield line


@attr.s(frozen=True, slots=True)
class Call(LValueExpression):
    """Represents an function call, i.e. ``my_function(arguments...)``.
    """
    function: Expression = attr.ib(validator=attr.validators.instance_of(Expression))
    arguments: typing.Sequence[Expression] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Expression),
            iterable_validator=attr.validators.instance_of(tuple),
        ),
        converter=tuple,
    )

    def render_expression(self):
        function_rendering = list(self.function.render_expression())

        for i, line in enumerate(function_rendering):
            if i == len(function_rendering) - 1:
                yield line, '('
            else:
                yield line

        for arg_index, argument in enumerate(self.arguments):
            argument_rendering = list(argument.render_expression())
            for i, line in enumerate(argument_rendering):
                if i == len(argument_rendering) - 1 and arg_index < len(self.arguments) - 1:
                    yield self.indent, line, ','
                else:
                    yield self.indent, line

        yield ')'


@attr.s(frozen=True, slots=True)
class Subscript(LValueExpression):
    """Represents an array subscript, i.e. ``my_array[123]``.
    """
    operand: Expression = attr.ib(validator=attr.validators.instance_of(Expression))
    subscript: Expression = attr.ib(validator=attr.validators.instance_of(Expression))

    def render_expression(self):
        operand_rendering = list(self.operand.render_expression())
        subscript_rendering = list(self.subscript.render_expression())
        subscript_rendering_iterator = iter(subscript_rendering)

        for i, line in enumerate(operand_rendering):
            if i == len(operand_rendering) - 1:
                if len(subscript_rendering) == 1:
                    # pylint: disable=stop-iteration-return
                    yield line, '[', next(subscript_rendering_iterator), ']'
                else:
                    # pylint: disable=stop-iteration-return
                    yield line, '[', next(subscript_rendering_iterator)
            else:
                yield line

        for i, line in enumerate(subscript_rendering_iterator):
            if i == len(operand_rendering) - 1:
                yield line, ']'
            else:
                yield line


@attr.s(frozen=True, slots=True)
class Arrow(LValueExpression):
    """Represents member dereference, i.e. ``my_struct.my_member``.
    """
    operand: Expression = attr.ib(validator=attr.validators.instance_of(Expression))
    member: str = attr.ib(validator=attr.validators.instance_of(str))

    def render_expression(self):
        operand_rendering = list(self.operand.render_expression())

        for i, line in enumerate(operand_rendering):
            if i == len(operand_rendering) - 1:
                yield line, '->', self.member
            else:
                yield line


@attr.s(frozen=True, slots=True)
class UnaryOperatorExpression(Expression):
    """Represents a unary operation on a single operand.
    """
    operand: Expression = attr.ib(validator=attr.validators.instance_of(Expression))

    operator = None  # override in subclass

    def render_expression(self):
        operand_rendering = list(self.operand.render_expression())

        for i, line in enumerate(operand_rendering):
            if i == 0 and len(operand_rendering) == 1:
                yield '(', self.operator, line, ')'
            elif i == 0:
                yield '(', self.operator, line
            elif i == len(operand_rendering) - 1:
                yield line, ')'
            else:
                yield line


@attr.s(frozen=True, slots=True)
class Increment(UnaryOperatorExpression):
    operator = '++'


@attr.s(frozen=True, slots=True)
class Decrement(UnaryOperatorExpression):
    operator = '--'


@attr.s(frozen=True, slots=True)
class AddressOf(UnaryOperatorExpression):
    operator = '&'


@attr.s(frozen=True, slots=True)
class Dereference(UnaryOperatorExpression, LValueExpression):
    operator = '*'


@attr.s(frozen=True, slots=True)
class Positive(UnaryOperatorExpression):
    operator = '+'


@attr.s(frozen=True, slots=True)
class Negative(UnaryOperatorExpression):
    operator = '-'


@attr.s(frozen=True, slots=True)
class BitwiseNot(UnaryOperatorExpression):
    operator = '~'


@attr.s(frozen=True, slots=True)
class Not(UnaryOperatorExpression):
    operator = '!'


@attr.s(frozen=True, slots=True)
class SizeOf(UnaryOperatorExpression):
    operator = 'sizeof '


@attr.s(frozen=True, slots=True)
class Cast(UnaryOperatorExpression):
    type: types.TypeBase = attr.ib(validator=attr.validators.instance_of(types.TypeBase))

    @property
    def operator(self):
        return '({})'.format(self.type.name)


@attr.s(frozen=True, slots=True)
class BinaryOperationExpression(Expression, metaclass=abc.ABCMeta):
    """Represents a binary operation between two operands.
    """
    left: Expression = attr.ib(validator=attr.validators.instance_of(Expression))
    right: Expression = attr.ib(validator=attr.validators.instance_of(Expression))

    operator = None  # override in subclass

    def render_expression(self):
        for i, line in enumerate(self.left.render_expression()):
            if i == 0:
                yield '(', line
            else:
                yield line

        right_rendering = list(self.right.render_expression())

        for i, line in enumerate(right_rendering):
            if i == 0 and len(right_rendering) == 1:
                yield self.indent, self.operator, ' ', line, ')'
            elif i == 0:
                yield self.indent, self.operator, ' ', line
            elif i == len(right_rendering) - 1:
                yield self.indent, line, ')'
            else:
                yield self.indent, line


@attr.s(frozen=True, slots=True)
class Assign(BinaryOperationExpression):
    """Represents an assignment.
    """
    left: LValueExpression = attr.ib(validator=attr.validators.instance_of(LValueExpression))
    right: Expression = attr.ib(validator=attr.validators.instance_of(Expression))

    operator = '='


@attr.s(frozen=True, slots=True)
class Multiply(BinaryOperationExpression):
    operator = '*'


@attr.s(frozen=True, slots=True)
class Mod(BinaryOperationExpression):
    operator = '%'


@attr.s(frozen=True, slots=True)
class Divide(BinaryOperationExpression):
    operator = '/'


@attr.s(frozen=True, slots=True)
class Add(BinaryOperationExpression):
    operator = '+'


@attr.s(frozen=True, slots=True)
class Subtract(BinaryOperationExpression):
    operator = '-'


@attr.s(frozen=True, slots=True)
class ShiftLeft(BinaryOperationExpression):
    operator = '<<'


@attr.s(frozen=True, slots=True)
class ShiftRight(BinaryOperationExpression):
    operator = '>>'


@attr.s(frozen=True, slots=True)
class LessThan(BinaryOperationExpression):
    operator = '<'


@attr.s(frozen=True, slots=True)
class GreaterThan(BinaryOperationExpression):
    operator = '>'


@attr.s(frozen=True, slots=True)
class LessThanOrEqual(BinaryOperationExpression):
    operator = '<='


@attr.s(frozen=True, slots=True)
class GreaterThanOrEqual(BinaryOperationExpression):
    operator = '>='


@attr.s(frozen=True, slots=True)
class Equals(BinaryOperationExpression):
    operator = '=='


@attr.s(frozen=True, slots=True)
class NotEquals(BinaryOperationExpression):
    operator = '!='


@attr.s(frozen=True, slots=True)
class BitwiseAnd(BinaryOperationExpression):
    operator = '&'


@attr.s(frozen=True, slots=True)
class BitwiseOr(BinaryOperationExpression):
    operator = '|'


@attr.s(frozen=True, slots=True)
class BitwiseXor(BinaryOperationExpression):
    operator = '^'


@attr.s(frozen=True, slots=True)
class And(BinaryOperationExpression):
    operator = '&&'


@attr.s(frozen=True, slots=True)
class Or(BinaryOperationExpression):
    operator = '||'
