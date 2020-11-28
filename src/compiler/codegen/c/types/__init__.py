from __future__ import annotations

import abc
import typing

import attr

from .. import include
from ... import c


@attr.s(frozen=True, slots=True)
class TypeBase(c.ProgramPartBase, metaclass=abc.ABCMeta):
    """Represents a types.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Get the name/identifier of this types.
        """
        raise NotImplementedError

    @property
    def pointer(self) -> Pointer:
        """Get a pointer to this types.
        """
        return Pointer(self)

    class_dependencies = (include.Include,)


@attr.s(frozen=True, slots=True)
class Void(TypeBase):
    """Represents a types with no data, void.
    """
    name = 'void'


@attr.s(frozen=True, slots=True)
class Pointer(TypeBase):
    """Represents a pointer types.
    """
    contained_type: TypeBase = attr.ib(validator=attr.validators.instance_of(TypeBase))

    @property
    def name(self):
        return '_{}_Ptr'.format(self.contained_type.name)

    @property
    def dependencies(self):
        yield self.contained_type

    def render_program_part(self):
        yield 'typedef {} *{};'.format(
            self.contained_type.name,
            self.name,
        )


@attr.s(frozen=True, slots=True)
class FunctionPointer(TypeBase):
    """Represents a function pointer types.
    """
    argument_types: typing.Sequence[TypeBase] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(TypeBase),
            iterable_validator=attr.validators.instance_of(tuple),
        ),
        converter=tuple,
    )
    return_type: TypeBase = attr.ib(validator=attr.validators.instance_of(TypeBase))

    @property
    def name(self):
        return '_{}_Returns_{}_FnPtr'.format(
            '_'.join(
                argument.name for argument in self.argument_types
            ),
            self.return_type.name
        )

    @property
    def dependencies(self):
        yield from self.argument_types
        yield self.return_type

    def render_program_part(self):
        yield 'typedef {} (*{})('.format(self.return_type.name, self.name)

        for i, argument_type in enumerate(self.argument_types):
            if i < len(self.argument_types) - 1:
                yield self.indent, argument_type.name, ','
            else:
                yield self.indent, argument_type.name

        yield ');'


@attr.s(frozen=True, slots=True)
class Struct(TypeBase):
    """Represents a struct type.
    """

    @attr.s(frozen=True, slots=True)
    class Field(object):
        """Represents a named and typed struct field.
        """
        name: str = attr.ib(validator=attr.validators.instance_of(str))
        type: TypeBase = attr.ib(validator=attr.validators.instance_of(TypeBase))

    name: str = attr.ib(
        validator=attr.validators.instance_of(str),
    )
    fields: typing.Sequence[Field] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Field),
            iterable_validator=attr.validators.instance_of(tuple),
        ),
        converter=tuple,
    )

    @property
    def dependencies(self):
        for field in self.fields:
            yield field.type

    def render_program_part(self):
        yield 'typedef struct {'

        for field in self.fields:
            yield self.indent, '{} {};'.format(
                field.type.name,
                field.name,
            )

        yield '} ', self.name, ';'


@attr.s(frozen=True, slots=True)
class Union(TypeBase):
    """Represents a union type.
    """

    @attr.s(frozen=True, slots=True)
    class Field(object):
        """Represents a named and typed union field.
        """
        name: str = attr.ib(validator=attr.validators.instance_of(str))
        type: TypeBase = attr.ib(validator=attr.validators.instance_of(TypeBase))

    name: str = attr.ib(
        validator=attr.validators.instance_of(str),
    )
    fields: typing.Sequence[Field] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Field),
            iterable_validator=attr.validators.instance_of(tuple),
        ),
        converter=tuple,
    )

    @property
    def dependencies(self):
        for field in self.fields:
            yield field.type

    def render_program_part(self):
        yield 'typedef union {'

        for field in self.fields:
            yield self.indent, '{} {};'.format(
                field.type.name,
                field.name,
            )

        yield '} ', self.name, ';'
