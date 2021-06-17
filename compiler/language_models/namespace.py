from __future__ import annotations

import typing

import attr


@attr.s(frozen=True, slots=True)
class Namespace:
    parent: typing.Optional[Namespace] = attr.ib(default=None)
    declarations: dict[str, typing.Any] = attr.ib(factory=dict, init=False)

    def lookup(self, name: str) -> typing.Any:
        if name in self.declarations:
            return self.declarations[name]

        if self.parent:
            return self.parent.lookup(name)

        raise KeyError(f'no such name {name!r}')

    def declare(self, name: str, value: typing.Any):
        self.declarations[name] = value

    def __getitem__(self, item):
        return self.lookup(item)
