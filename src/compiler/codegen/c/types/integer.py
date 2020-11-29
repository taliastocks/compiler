from __future__ import annotations

import abc

import attr

from .. import include, types


@attr.s(frozen=True, slots=True)
class IntBase(types.TypeBase, metaclass=abc.ABCMeta):
    """Base class for integer types.
    """
    _name: str = None  # Override in subclass.

    @property
    def name(self):
        return self._name


@attr.s(frozen=True, slots=True)
class SizeT(IntBase):
    """Alias of one of the fundamental unsigned integer types.

    It is a type able to represent the size of any object in bytes: size_t is the
    type returned by the sizeof operator and is widely used in the standard library
    to represent sizes and counts.
    """
    signed = False
    _name = 'size_t'

    @property
    def dependencies(self):
        yield include.Include(path='stddef.h', builtin=True)


@attr.s(frozen=True, slots=True)
class WCharT(IntBase):
    """Can represent the largest supported character set.
    """
    signed = False
    _name = 'wchar_t'

    @property
    def dependencies(self):
        yield include.Include(path='stddef.h', builtin=True)


@attr.s(frozen=True, slots=True)
class UCharBase(IntBase, metaclass=abc.ABCMeta):
    """Base class for unicode character types.
    """
    signed = False

    @property
    def dependencies(self):
        yield include.Include(path='uchar.h', builtin=True)


@attr.s(frozen=True, slots=True)
class Char16T(UCharBase):
    """Not smaller than char. At least 16 bits.
    """
    _name = 'char16_t'


@attr.s(frozen=True, slots=True)
class Char32T(UCharBase):
    """Not smaller than char16_t. At least 32 bits.
    """
    _name = 'char32_t'


@attr.s(frozen=True, slots=True)
class FundamentalIntBase(IntBase, metaclass=abc.ABCMeta):
    """Base class for fundamental integer types.
    """
    signed: bool = attr.ib(validator=attr.validators.instance_of(bool), default=True)

    @property
    def name(self):
        return ('' if self.signed else 'unsigned_') + self._name

    def render_program_part(self):
        if '_' in self.name:  # Create an alias type without the inconvenient spaces.
            yield 'typedef {} {};'.format(
                self.name.replace('_', ' '),
                self.name
            )


@attr.s(frozen=True, slots=True)
class Char(FundamentalIntBase):
    """Exactly one byte in size. At least 8 bits.
    """
    _name = 'char'


@attr.s(frozen=True, slots=True)
class Short(FundamentalIntBase):
    """Not smaller than char. At least 16 bits.
    """
    _name = 'short'


@attr.s(frozen=True, slots=True)
class Int(FundamentalIntBase):
    """Not smaller than short. At least 16 bits.
    """
    _name = 'int'


@attr.s(frozen=True, slots=True)
class Long(FundamentalIntBase):
    """Not smaller than int. At least 32 bits.
    """
    _name = 'long'


@attr.s(frozen=True, slots=True)
class LongLong(FundamentalIntBase):
    """Not smaller than long. At least 64 bits.
    """
    _name = 'long_long'


@attr.s(frozen=True, slots=True)
class StdIntBase(IntBase, metaclass=abc.ABCMeta):
    """Base class for integer types defined in stdint.h.
    """
    signed: bool = attr.ib(validator=attr.validators.instance_of(bool), default=True)

    @property
    def name(self):
        return ('' if self.signed else 'u') + self._name

    @property
    def dependencies(self):
        yield include.Include(path='stdint.h', builtin=True)


@attr.s(frozen=True, slots=True)
class IntMaxT(StdIntBase):
    """Integer type with the maximum width supported.
    """
    _name = 'intmax_t'


@attr.s(frozen=True, slots=True)
class IntPtrT(StdIntBase):
    """Integer type capable of holding a value converted from a void pointer
    and then be converted back to that type with a value that compares equal
    to the original pointer.
    """
    _name = 'intptr_t'


@attr.s(frozen=True, slots=True)
class Int8T(StdIntBase):
    """Integer type with a width of exactly 8 bits.
    """
    _name = 'int8_t'


@attr.s(frozen=True, slots=True)
class Int16T(StdIntBase):
    """Integer type with a width of exactly 16 bits.
    """
    _name = 'int16_t'


@attr.s(frozen=True, slots=True)
class Int32T(StdIntBase):
    """Integer type with a width of exactly 32 bits.
    """
    _name = 'int32_t'


@attr.s(frozen=True, slots=True)
class Int64T(StdIntBase):
    """Integer type with a width of exactly 64 bits.
    """
    _name = 'int64_t'


@attr.s(frozen=True, slots=True)
class IntLeast8T(StdIntBase):
    """Integer type with a width of at least 8 bits.
    No other integer type exists with lesser size and at least the specified width.
    """
    _name = 'int_least8_t'


@attr.s(frozen=True, slots=True)
class IntLeast16T(StdIntBase):
    """Integer type with a width of at least 16 bits.
    No other integer type exists with lesser size and at least the specified width.
    """
    _name = 'int_least16_t'


@attr.s(frozen=True, slots=True)
class IntLeast32T(StdIntBase):
    """Integer type with a width of at least 32 bits.
    No other integer type exists with lesser size and at least the specified width.
    """
    _name = 'int_least32_t'


@attr.s(frozen=True, slots=True)
class IntLeast64T(StdIntBase):
    """Integer type with a width of at least 64 bits.
    No other integer type exists with lesser size and at least the specified width.
    """
    _name = 'int_least64_t'


@attr.s(frozen=True, slots=True)
class IntFast8T(StdIntBase):
    """Integer type with a width of at least 8 bits.
    At least as fast as any other integer type with at least the specified width.
    """
    _name = 'int_fast8_t'


@attr.s(frozen=True, slots=True)
class IntFast16T(StdIntBase):
    """Integer type with a width of at least 16 bits.
    At least as fast as any other integer type with at least the specified width.
    """
    _name = 'int_fast16_t'


@attr.s(frozen=True, slots=True)
class IntFast32T(StdIntBase):
    """Integer type with a width of at least 32 bits.
    At least as fast as any other integer type with at least the specified width.
    """
    _name = 'int_fast32_t'


@attr.s(frozen=True, slots=True)
class IntFast64T(StdIntBase):
    """Integer type with a width of at least 64 bits.
    At least as fast as any other integer type with at least the specified width.
    """
    _name = 'int_fast64_t'
