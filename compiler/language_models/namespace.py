from __future__ import annotations

import typing

import attr


@attr.s(frozen=True, slots=True)
class Namespace:
    parent: typing.Optional[Namespace] = attr.ib(default=None)
    declarations: typing.MutableMapping[str, typing.Any] = attr.ib(factory=dict, init=False)

    def lookup(self, name: str) -> typing.Any:
        if name in self.declarations:
            return self.declarations[name]

        if self.parent:
            return self.parent.lookup(name)

        raise KeyError('no such name {!r}'.format(name))

    def declare(self, name: str, value: typing.Any):
        if name in self.declarations:
            raise KeyError('name {!r} already defined'.format(name))

        self.declarations[name] = value
