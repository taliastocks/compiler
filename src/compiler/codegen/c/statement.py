import abc
import typing

import attr

from .. import c
from . import expression as expression_module, types


@attr.s(frozen=True, slots=True)
class Statement(c.ProgramPartBase, metaclass=abc.ABCMeta):
    """Represents a statement.
    """

    @abc.abstractmethod
    def render_statement(self) -> typing.Generator[str, None, None]:
        """Render the statement.
        """
        raise NotImplementedError


@attr.s(frozen=True, slots=True)
class DeclarationStatement(Statement):
    """Represents a variable declaration.
    """
    name: str = attr.ib(validator=attr.validators.instance_of(str))
    type: types.TypeBase = attr.ib(validator=attr.validators.instance_of(types.TypeBase))

    @property
    def dependencies(self):
        yield self.type

    def render_statement(self):
        yield self.type.name, ' ', self.name, ';'


@attr.s(frozen=True, slots=True)
class ExpressionStatement(Statement):
    """Represents a statement consisting of an expression.
    """
    expression: expression_module.Expression = attr.ib(
        validator=attr.validators.instance_of(expression_module.Expression)
    )

    def render_statement(self):
        last_line = None

        for line in self.expression.render_expression():
            if last_line is not None:
                yield last_line
            last_line = line

        yield last_line, ';'


@attr.s(frozen=True, slots=True)
class ReturnStatement(Statement):
    """Represents a return statement.
    """
    expression: typing.Optional[expression_module.Expression] = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(expression_module.Expression)),
        default=None,
    )

    def render_statement(self):
        if self.expression is None:
            yield 'return;'
        else:
            rendering = list(self.expression.render_expression())

            for i, line in enumerate(rendering):
                if len(rendering) == 1:
                    yield 'return ', line, ';'
                elif i == 0:
                    yield 'return ', line
                elif i == len(rendering) - 1:
                    yield line, ';'
                else:
                    yield line


@attr.s(frozen=True, slots=True)
class ContinueStatement(Statement):
    """Represents a continue statement.
    """

    def render_statement(self):
        yield 'continue;'


@attr.s(frozen=True, slots=True)
class BreakStatement(Statement):
    """Represents a break statement.
    """

    def render_statement(self):
        yield 'break;'


@attr.s(frozen=True, slots=True)
class BlockStatement(Statement):
    """Represents a code block.
    """
    statements: typing.Sequence[Statement] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Statement),
            iterable_validator=attr.validators.instance_of(tuple),
        ),
        converter=tuple,
    )

    def render_statement(self):
        yield '{'

        for statement in self.statements:
            for line in statement.render_statement():
                yield self.indent, line

        yield '}'


@attr.s(frozen=True, slots=True)
class IfStatement(Statement):
    """Represents an if statement.
    """
    condition: expression_module.Expression = attr.ib(
        validator=attr.validators.instance_of(expression_module.Expression)
    )
    if_true: Statement = attr.ib(validator=attr.validators.instance_of(Statement))
    if_false: typing.Optional[Statement] = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(Statement)),
        default=None,
    )

    def render_statement(self):
        yield 'if ('
        for line in self.condition.render_expression():
            yield self.indent, line

        for i, line in enumerate(self.if_true.render_statement()):
            if i == 0:
                yield ') ', line
            else:
                yield line

        if self.if_false is not None:
            for i, line in enumerate(self.if_false.render_statement()):
                if i == 0:
                    yield 'else ', line
                else:
                    yield line


@attr.s(frozen=True, slots=True)
class WhileStatement(Statement):
    """Represents a while statement.
    """
    condition: expression_module.Expression = attr.ib(
        validator=attr.validators.instance_of(expression_module.Expression)
    )
    body: Statement = attr.ib(validator=attr.validators.instance_of(Statement))

    def render_statement(self):
        yield 'while ('
        for line in self.condition.render_expression():
            yield self.indent, line

        for i, line in enumerate(self.body.render_statement()):
            if i == 0:
                yield ') ', line
            else:
                yield line


@attr.s(frozen=True, slots=True)
class DoWhileStatement(Statement):
    """Represents a "do while" statement.
    """
    condition: expression_module.Expression = attr.ib(
        validator=attr.validators.instance_of(expression_module.Expression)
    )
    body: Statement = attr.ib(validator=attr.validators.instance_of(Statement))

    def render_statement(self):
        for i, line in enumerate(self.body.render_statement()):
            if i == 0:
                yield 'do', line
            else:
                yield line

        yield 'while ('
        for line in self.condition.render_expression():
            yield self.indent, line
        yield ');'


@attr.s(frozen=True, slots=True)
class SwitchStatement(Statement):
    """Represents a switch statement.
    """
    @attr.s(frozen=True, slots=True)
    class Case:
        values: typing.Collection[expression_module.IntegerLiteral] = attr.ib(
            validator=attr.validators.deep_iterable(
                member_validator=attr.validators.instance_of(expression_module.IntegerLiteral),
                iterable_validator=attr.validators.instance_of(frozenset),
            ),
            converter=frozenset,
        )
        consequence: Statement = attr.ib(validator=attr.validators.instance_of(Statement))

    switch: expression_module.Expression = attr.ib(
        validator=attr.validators.instance_of(expression_module.Expression)
    )
    cases: typing.Sequence[Case] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Case),
            iterable_validator=attr.validators.instance_of(tuple),
        ),
        converter=tuple,
    )
    default: typing.Optional[Statement] = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(Statement)),
        default=None,
    )

    def render_statement(self):
        yield 'switch ('
        for line in self.switch.render_expression():
            yield self.indent, line
        yield ') {'

        for case in self.cases:
            for integer_literal_expression in sorted(case.values):
                for line in integer_literal_expression.render_expression():
                    yield self.indent, 'case ', line, ':'

            for line in case.consequence.render_statement():
                yield self.indent, self.indent, line

            yield self.indent, self.indent, 'break;'

        if self.default is not None:
            yield self.indent, 'default:'

            for line in self.default.render_statement():
                yield self.indent, self.indent, line

        yield '}'
