from __future__ import annotations

import collections
import typing

import attr

from .meta import instance_cache


@attr.s(frozen=True, slots=True)
class TypeBase(metaclass=instance_cache.InstanceCacheABCMeta):
    """A type should be thought of as a set of possible values.

    Types may be defined in terms of other types. For example, Union([T1, T2]) is a
    type which can take on all the values in T1 as well as all the values in T2. Types
    may also be composed of other types, for example a function type is composed of its
    argument types and return types.

    Note that to simplify implementation, some types may define Union([T1, T2]) to be a
    strict superset of T1 and T2. For example, Integer() types track only the maximum and
    minimum representable values when combined with Union().
    """

    @staticmethod
    def unify(types: typing.Collection[TypeBase]) -> typing.Collection[TypeBase]:
        """Combine one or more types together if possible; otherwise return them unchanged.

        Types are expected to all be instances of the same Type class.
        """
        return set(types)  # Default implementation: remove any duplicates.


@attr.s(frozen=True, slots=True)
class Union(TypeBase):
    """Type operator which combines types together. The resulting type can take on any
    value representable by any of its component types.
    """
    subtypes: typing.Collection[TypeBase] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(TypeBase),
            iterable_validator=attr.validators.instance_of(frozenset),
        ),
        converter=frozenset,
    )

    def __new__(cls, subtypes):
        """Unify subtypes before instantiating a Union.
        If Any() is in subtypes, return Any().
        """
        # Group types by class, extracting types from any unions as we go.
        # If we encounter Any(), return it immediately, as it encompasses all possible types.
        subtypes_by_class: typing.Dict[typing.Type[TypeBase], typing.Set[TypeBase]] = collections.defaultdict(set)
        for subtype in subtypes:
            if isinstance(subtype, Any):
                return subtype

            if isinstance(subtype, Union):
                for subsubtype in subtype.subtypes:
                    subtypes_by_class[type(subsubtype)].add(subsubtype)
            else:
                subtypes_by_class[type(subtype)].add(subtype)

        # Unify types of the same class into a final set of types.
        final_subtypes = set()
        for subtype_class, subtypes_of_same_class in subtypes_by_class.items():
            final_subtypes.update(subtype_class.unify(subtypes_of_same_class))

        # If there's only one type, no need to wrap it in a Union.
        if len(final_subtypes) == 1:
            return next(iter(final_subtypes))

        # Otherwise, create a new Union of the final subtypes and return it.
        return super().__new__(cls, final_subtypes)


@attr.s(frozen=True, slots=True)
class Any(TypeBase):
    """Type encompassing all possible values representable in a program. This type can
    be thought of as a Union of all other types.
    """


@attr.s(frozen=True, slots=True)
class NoneValue(TypeBase):
    """Type capable of representing None.
    """


@attr.s(frozen=True, slots=True)
class FalseValue(TypeBase):
    """Type capable of representing False.
    """


@attr.s(frozen=True, slots=True)
class TrueValue(TypeBase):
    """Type capable of representing True.
    """


Boolean = Union([FalseValue, TrueValue])


@attr.s(frozen=True, slots=True)
class Integer(TypeBase):
    """Type capable of representing integers in the range [minimum_value, maximum_value].
    Unions of Integer types take on the most extreme minimum_value and maximum_value.
    """
    minimum_value: typing.Optional[int] = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(int))
    )
    maximum_value: typing.Optional[int] = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(int))
    )

    @staticmethod
    def unify(types: typing.Collection[Integer]) -> typing.Collection[Integer]:
        types_iter = iter(types)
        first_integer = next(types_iter)

        minimum_value = first_integer.minimum_value
        maximum_value = first_integer.maximum_value

        for integer in types:
            assert isinstance(integer, Integer)
            # Record the most extreme [minimum_value, maximum_value].
            if integer.minimum_value is None:
                minimum_value = None
            elif minimum_value is not None:
                minimum_value = min(minimum_value, integer.minimum_value)

            if integer.maximum_value is None:
                maximum_value = None
            elif maximum_value is not None:
                maximum_value = max(maximum_value, integer.maximum_value)

        return {Integer(
            minimum_value=minimum_value,
            maximum_value=maximum_value,
        )}

    @maximum_value.validator
    def _check_min_less_than_max(self, _, __):
        if self.minimum_value is not None and self.maximum_value is not None:
            if self.minimum_value > self.maximum_value:
                raise ValueError('expected minimum_value <= maximum_value, got {} > {}'.format(
                    self.minimum_value,
                    self.maximum_value,
                ))
