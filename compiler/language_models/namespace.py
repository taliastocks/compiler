from __future__ import annotations

import typing

import attr

from compiler.language_models import declarable


@attr.s(frozen=True, slots=True)
class Namespace:
    parent: typing.Optional[Namespace] = attr.ib(default=None)
    declarations: typing.Mapping[str, declarable.Declarable] = attr.ib(factory=dict, init=False)

    def lookup(self, name: str) -> typing.Optional[declarable.Declarable]:
        if name in self.declarations:
            return self.declarations[name]

        if self.parent:
            return self.parent.lookup(name)

        return None

    def declare(self, value: declarable.Declarable):
        if value.name in self.declarations:
            raise KeyError('name {!r} already defined'.format(value.name))

        self.declarations[value.name] = value
