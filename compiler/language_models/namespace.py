from __future__ import annotations

import typing

import attr


@attr.s(frozen=True, slots=True)
class Namespace:
    parent: typing.Optional[Namespace] = attr.ib(default=None)
    program: typing.Optional[program_module.Program] = attr.ib()
    module_path: typing.Sequence[str] = attr.ib(converter=tuple)
    declarations: dict[str, typing.Any] = attr.ib(factory=dict, init=False)

    @attr.s(frozen=True, slots=True)
    class Object:
        __namespace: Namespace = attr.ib()

        def __getattr__(self, item):
            return self.__namespace[item]

    def as_object(self):
        return Namespace.Object(self)

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

    @program.default
    def _init_program(self):
        if self.parent is not None:
            return self.parent.program
        return None

    @module_path.default
    def _init_module_path(self):
        if self.parent is not None:
            return self.parent.module_path
        return ()


from . import program as program_module  # noqa, pylint: disable=cyclic-import, wrong-import-position
