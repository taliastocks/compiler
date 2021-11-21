from __future__ import annotations

import typing

import attr

from . import program, types, statement, include


@attr.s(frozen=True, slots=True)
class Function(program.ProgramPartBase):
    """Represents a function.
    """

    @attr.s(frozen=True, slots=True)
    class Argument:
        """Represents a named and typed function argument.
        """
        name: str = attr.ib(validator=attr.validators.instance_of(str))
        type: types.TypeBase = attr.ib(validator=attr.validators.instance_of(types.TypeBase))

    @attr.s(frozen=True, slots=True)
    class ForwardDeclaration(program.ProgramPartBase):
        name: str = attr.ib(validator=attr.validators.instance_of(str))
        argument_types: typing.Sequence[types.TypeBase] = attr.ib(
            validator=attr.validators.deep_iterable(
                member_validator=attr.validators.instance_of(types.TypeBase),
                iterable_validator=attr.validators.instance_of(tuple),
            ),
            converter=tuple,
        )
        return_type: types.TypeBase = attr.ib(validator=attr.validators.instance_of(types.TypeBase))

        @property
        def dependencies(self):
            yield from self.argument_types
            yield self.return_type

        def render_program_part(self):
            yield f'{self.return_type.name} {self.name}('

            for i, argument_type in enumerate(self.argument_types):
                if i == len(self.argument_types) - 1:
                    yield self.indent, argument_type.name
                else:
                    yield self.indent, argument_type.name, ','

            yield ');'

    name: str = attr.ib(validator=attr.validators.instance_of(str))
    arguments: typing.Sequence[Function.Argument] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Argument),
            iterable_validator=attr.validators.instance_of(tuple),
        ),
        converter=tuple,
    )
    return_type: types.TypeBase = attr.ib(validator=attr.validators.instance_of(types.TypeBase))
    statements: typing.Sequence[statement.Statement] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(statement.Statement),
            iterable_validator=attr.validators.instance_of(tuple),
        ),
        converter=tuple,
    )

    @property
    def pointer_type(self):
        return types.FunctionPointer(
            argument_types=[arg.type for arg in self.arguments],
            return_type=self.return_type,
        )

    @property
    def forward_declaration(self):
        return Function.ForwardDeclaration(
            name=self.name,
            argument_types=[argument.type for argument in self.arguments],
            return_type=self.return_type,
        )

    class_dependencies = (include.Include, ForwardDeclaration)

    @property
    def dependencies(self):
        yield self.forward_declaration
        yield from self.statements

    def render_program_part(self):
        yield f'{self.return_type.name} {self.name}('

        for i, argument in enumerate(self.arguments):
            if i == len(self.arguments) - 1:
                yield self.indent, argument.type.name, ' ', argument.name
            else:
                yield self.indent, argument.type.name, ' ', argument.name, ','

        yield ') {'

        for statement_ in self.statements:
            for line in statement_.render_statement():
                yield self.indent, line

        yield '}'
