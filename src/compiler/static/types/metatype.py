import typing

import attr
import frozendict

from ...meta import instance_cache


@attr.s(frozen=True, slots=True)
class TypeBase(metaclass=instance_cache.InstanceCacheABCMeta):
    name: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(frozen=True, slots=True)
class Union(TypeBase):
    types: typing.Collection = attr.ib(
        validator=attr.validators.instance_of(frozenset),
        converter=frozenset,
    )


@attr.s(frozen=True, slots=True)
class Struct(TypeBase):
    fields: typing.Mapping[str, TypeBase] = attr.ib(
        validator=attr.validators.deep_mapping(
            key_validator=attr.validators.instance_of(str),
            value_validator=attr.validators.instance_of(TypeBase),
            mapping_validator=attr.validators.instance_of(dict),
        ),
        converter=frozendict.frozendict,
    )


@attr.s(frozen=True, slots=True)
class Singleton(TypeBase):
    pass


@attr.s(frozen=True, slots=True)
class Integer(TypeBase):
    minimum: typing.Optional[int] = attr.ib(validator=attr.validators.optional(attr.validators.instance_of(int)))
    maximum: typing.Optional[int] = attr.ib(validator=attr.validators.optional(attr.validators.instance_of(int)))

    @maximum.validator
    def _check_maximum(self, _, __):
        if self.minimum is not None and self.maximum is not None:
            if self.minimum > self.maximum:
                raise ValueError('expected minimum <= maximum, got {!r} > {!r}'.format(self.minimum, self.maximum))


@attr.s(frozen=True, slots=True)
class Array(TypeBase):
    item_type: TypeBase = attr.ib(validator=attr.validators.instance_of(TypeBase))
    length_type: Integer = attr.ib(validator=attr.validators.instance_of(Integer))


@attr.s(frozen=True, slots=True)
class String(TypeBase):
    pass
