from __future__ import annotations

import typing

import attr
import immutabledict

from . import declarable as declarable_module, function as function_module, class_ as class_module


@attr.s(frozen=True, slots=True)
class Module:
    path: typing.Sequence[str] = attr.ib(converter=tuple, repr=False)
    imports: typing.Collection[Import] = attr.ib(converter=frozenset, repr=False)
    functions: typing.Collection[function_module.Function] = attr.ib(converter=frozenset, repr=False)
    classes: typing.Collection[class_module.Class] = attr.ib(converter=frozenset, repr=False)

    globals: typing.Mapping[declarable_module.Declarable] = attr.ib(converter=immutabledict.immutabledict,
                                                                    init=False,
                                                                    repr=False)

    @globals.default
    def _init_globals(self):
        global_declarations = {}

        for declarables in [self.imports, self.functions, self.classes]:
            for declarable in declarables:
                if declarable.name in global_declarations:
                    raise ValueError('{!r} cannot be declared with the same name as {!r}'.format(
                        declarable,
                        global_declarations[declarable.name]
                    ))
                global_declarations[declarable.name] = declarable

        return global_declarations


@attr.s(frozen=True, slots=True)
class Import(declarable_module.Declarable):
    path: typing.Sequence[str] = attr.ib(converter=tuple, repr=False)
