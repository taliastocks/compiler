import typing

import attr


@attr.s(frozen=True, slots=True)
class Value:
    """Represents the value of a variable, argument, return value, or a struct field.
    """
    name: typing.Optional[str] = attr.ib(default=None)
