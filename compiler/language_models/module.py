from __future__ import annotations

import typing

import attr
import immutabledict

from . import (
    class_ as class_module,
    declarable as declarable_module,
    expression,
    function as function_module,
    reference as path_module,
)
from .. import grammar


@attr.s(frozen=True, slots=True)
class Module(grammar.NonTerminal):
    imports: typing.Collection[Import] = attr.ib(converter=frozenset, default=(), repr=False)
    functions: typing.Collection[function_module.Function] = attr.ib(converter=frozenset, default=(), repr=False)
    classes: typing.Collection[class_module.Class] = attr.ib(converter=frozenset, default=(), repr=False)
    variables: typing.Collection[expression.Variable] = attr.ib(converter=frozenset, default=(), repr=False)

    globals: typing.Mapping[declarable_module.Declarable] = attr.ib(converter=immutabledict.immutabledict,
                                                                    init=False,
                                                                    repr=False)

    @classmethod
    def production_rules(cls):
        yield [grammar.repeated(
            grammar.one_of(Import, function_module.Function, class_module.Class, expression.Variable)
        )]

    @classmethod
    def from_string(cls, name: str, code: str):
        pass

    @globals.default
    def _init_globals(self):
        global_declarations = {}

        for declarables in [self.imports, self.functions, self.classes, self.variables]:
            for declarable in declarables:
                if declarable.name in global_declarations:
                    raise ValueError('{!r} cannot be declared with the same name as {!r}'.format(
                        declarable,
                        global_declarations[declarable.name]
                    ))
                global_declarations[declarable.name] = declarable

        return global_declarations


@attr.s(frozen=True, slots=True)
class Import(declarable_module.Declarable, grammar.NonTerminal):
    path: path_module.ModuleReference = attr.ib()

    @classmethod
    def production_rules(cls):
        # Placeholder until I get around to writing a real implementation.
        yield from []
