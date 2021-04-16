from __future__ import annotations

import typing

import attr
import immutabledict

from . import (
    declarable as declarable_module,
    statement as statement_module,
)
from ..lib import parser as parser_module


@attr.s(frozen=True, slots=True)
class Module(parser_module.Symbol):
    statements: typing.Sequence[statement_module.Statement] = attr.ib(converter=tuple)
    globals: typing.Mapping[declarable_module.Declarable] = attr.ib(converter=immutabledict.immutabledict,
                                                                    init=False,
                                                                    repr=False)

    @classmethod
    def from_string(cls, code: str):
        cursor = parser_module.Cursor(code.splitlines())

        return cls.parse(cursor).last_symbol

    @classmethod
    def parse(cls, cursor: parser_module.Cursor):
        statements: list[statement_module.Statement] = []

        while not isinstance(cursor.last_symbol, parser_module.EndFile):
            cursor = cursor.parse_one_symbol([
                parser_module.EndFile,
                statement_module.Statement,
            ])
            if isinstance(cursor.last_symbol, statement_module.Statement):
                statements.append(cursor.last_symbol)
            else:  # EndFile
                break

        return cursor.new_from_symbol(cls(
            cursor=cursor,
            statements=statements,
        ))

    @globals.default
    def _init_globals(self):
        global_declarations = {}

        for statement in self.statements:
            for receiver in statement.receivers:
                if isinstance(receiver, declarable_module.Declarable):
                    declarable: declarable_module.Declarable = receiver
                    if declarable.name in global_declarations:
                        raise ValueError('{!r} cannot be declared with the same name as {!r}'.format(
                            declarable,
                            global_declarations[declarable.name]
                        ))
                    global_declarations[declarable.name] = declarable

        return global_declarations
