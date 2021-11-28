from __future__ import annotations

import typing

import attr

from . import (
    statement as statement_module,
    namespace as namespace_module,
)
from ..libs import parser as parser_module


builtin_namespace = namespace_module.Namespace()
builtin_namespace.declare('print', print)


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

    def execute(self,
                program: typing.Optional[program_module.Program] = None,
                path: typing.Sequence[str] = ()):
        """Get a runtime module object.
        """
        if program is None:
            program = program_module.Program()

        global_namespace = namespace_module.Namespace(
            parent=builtin_namespace,
            program=program,
            module_path=path,
        )

        with statement_module.Raise.Outcome.catch(self) as get_outcome:
            for statement in self.statements:
                statement.execute(global_namespace).get_value()

        get_outcome().get_value()  # reraise any exception, with module added to traceback

        return global_namespace.as_object()


from . import program as program_module  # noqa, pylint: disable=cyclic-import, wrong-import-position
