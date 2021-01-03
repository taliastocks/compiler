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
from .. import parser as parser_module


@attr.s(frozen=True, slots=True)
class Module(parser_module.Symbol):
    imports: typing.Collection[Import] = attr.ib(converter=frozenset, default=(), repr=False)
    functions: typing.Collection[function_module.Function] = attr.ib(converter=frozenset, default=(), repr=False)
    classes: typing.Collection[class_module.Class] = attr.ib(converter=frozenset, default=(), repr=False)
    variables: typing.Collection[expression.Variable] = attr.ib(converter=frozenset, default=(), repr=False)

    globals: typing.Mapping[declarable_module.Declarable] = attr.ib(converter=immutabledict.immutabledict,
                                                                    init=False,
                                                                    repr=False)

    @classmethod
    def from_string(cls, code: str):
        pass

    @classmethod
    def parse(cls, parser: parser_module.Parser):
        imports = []
        functions = []
        classes = []
        variables = []

        while not isinstance(parser.last_symbol, parser_module.EndFile):
            parser = parser.parse([
                parser_module.EndFile,
                Import,
                function_module.Function,
                class_module.Class,
                expression.Variable,
            ])
            if isinstance(parser.last_symbol, Import):
                imports.append(parser.last_symbol)
            elif isinstance(parser.last_symbol, function_module.Function):
                functions.append(parser.last_symbol)
            elif isinstance(parser.last_symbol, class_module.Class):
                classes.append(parser.last_symbol)
            elif isinstance(parser.last_symbol, expression.Variable):
                variables.append(parser.last_symbol)

        return parser.new_from_symbol(cls(
            imports=imports,
            functions=functions,
            classes=classes,
            variables=variables,
        ))

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
class Import(declarable_module.Declarable, parser_module.Symbol):
    path: path_module.ModuleReference = attr.ib()

    @classmethod
    def parse(cls, parser):
        pass  # Placeholder until I get around to writing a real implementation.
