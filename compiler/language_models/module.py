from __future__ import annotations

import typing

import attr
import immutabledict

from . import (
    statement as statement_module,
    namespace as namespace_module,
)
from ..libs import parser as parser_module


class _String(str):
    is_alpha = str.isalpha
    is_digit = str.isdigit
    is_numeric = str.isnumeric
    is_decimal = str.isdecimal
    is_alphanumeric = str.isalnum
    is_space = str.isspace


builtin_namespace = namespace_module.Namespace()
builtin_namespace.declare('True', True)
builtin_namespace.declare('False', False)
builtin_namespace.declare('None', None)
builtin_namespace.declare('RuntimeError', RuntimeError)
builtin_namespace.declare('ValueError', ValueError)
builtin_namespace.declare('TypeError', TypeError)
builtin_namespace.declare('Exception', Exception)
builtin_namespace.declare('print', print)
builtin_namespace.declare('Boolean', bool)
builtin_namespace.declare('String', _String)
builtin_namespace.declare('Character', str)
builtin_namespace.declare('Integer', int)
builtin_namespace.declare('List', list)
builtin_namespace.declare('FrozenList', tuple)
builtin_namespace.declare('Set', set)
builtin_namespace.declare('FrozenSet', frozenset)
builtin_namespace.declare('Map', dict)
builtin_namespace.declare('FrozenMap', immutabledict.immutabledict)
builtin_namespace.declare('type', type)
builtin_namespace.declare('range', range)
builtin_namespace.declare('Class', typing.Type)
builtin_namespace.declare('Union', typing.Union)
builtin_namespace.declare('issubclass', issubclass)
builtin_namespace.declare('isinstance', isinstance)
builtin_namespace.declare('staticmethod', staticmethod)
builtin_namespace.declare('classmethod', classmethod)
builtin_namespace.declare('abstract', lambda x: x)  # don't bother implementing yet


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
                parser_module.EndLine,
                statement_module.Statement,
            ])
            if isinstance(cursor.last_symbol, statement_module.Statement):
                statements.append(cursor.last_symbol)
            elif isinstance(cursor.last_symbol, parser_module.EndLine):
                continue
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
