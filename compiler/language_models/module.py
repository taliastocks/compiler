from __future__ import annotations

import typing

import attr
import immutabledict

from . import (
    declarable as declarable_module,
    statement as statement_module,
    namespace as namespace_module,
)
from ..libs import parser as parser_module


@attr.s(frozen=True, slots=True)
class Module(parser_module.Symbol):
    statements: typing.Sequence[statement_module.Statement] = attr.ib(converter=tuple)

    @classmethod
    def from_string(cls, code: str) -> Module:
        cursor = parser_module.Cursor(code.splitlines())

        return cls.parse(cursor).last_symbol  # noqa

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

    def execute(self):
        """Get a runtime module object.
        """
        global_namespace = namespace_module.Namespace()

        with statement_module.Raise.Outcome.catch(self) as get_outcome:
            for statement in self.statements:
                statement.execute(global_namespace)

        get_outcome().get_value()  # reraise any exception, with module added to traceback

        return global_namespace.as_object()
