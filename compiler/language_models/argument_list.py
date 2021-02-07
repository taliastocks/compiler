from __future__ import annotations

import typing

import attr

from .. import parser as parser_module


@attr.s(frozen=True, slots=True)
class ArgumentList(parser_module.Symbol):
    """A list of function arguments.

    Why is this here? This isn't an Expression!

        Although ArgumentList is not an expression, it participates in a dependency
        cycle with Lambda and Variable. Since Python makes module dependency cycles
        difficult, this goes here for now. When the compiler is rewritten in Sibilance,
        this class and Argument should both move to a new module.
    """
    arguments: typing.Sequence[Argument] = attr.ib(converter=tuple, default=())

    @classmethod
    def parse(cls, cursor, parse_annotations: bool = True):
        # pylint: disable=too-many-branches, arguments-differ
        arguments: list[Argument] = []
        saw_end_position_only_marker = False
        saw_begin_keyword_only_marker = False
        saw_extra_positionals = False
        saw_extra_keywords = False

        while True:
            cursor = cursor.parse_one_symbol([
                parser_module.Characters['**'],
                parser_module.Characters['*'],
                parser_module.Characters['/'],
                parser_module.Always,
            ])

            new_cursor = expression.Variable.parse(
                cursor=cursor,
                parse_annotation=parse_annotations,
                parse_initializer=True,
            )

            if isinstance(cursor.last_symbol, parser_module.Characters['*']):
                if new_cursor is not None and isinstance(new_cursor.last_symbol, expression.Variable):
                    # This is "extra positional args" (which also acts as a keyword-only marker).
                    if saw_extra_positionals:
                        raise parser_module.ParseError('multiple "extra positional" arguments found', cursor)
                    saw_extra_positionals = True

                    arguments.append(Argument(
                        variable=new_cursor.last_symbol,
                        is_positional=True,
                        is_extra=True,
                    ))
                    cursor = new_cursor

                if saw_begin_keyword_only_marker:
                    raise parser_module.ParseError('multiple "begin keyword-only" markers found', cursor)
                saw_begin_keyword_only_marker = True

            elif isinstance(cursor.last_symbol, parser_module.Characters['**']):
                if new_cursor is None or not isinstance(new_cursor.last_symbol, expression.Variable):
                    raise parser_module.ParseError('expected Variable', cursor)
                if saw_extra_keywords:
                    raise parser_module.ParseError('multiple "extra keyword" arguments found', cursor)
                saw_extra_keywords = True

                arguments.append(Argument(
                    variable=new_cursor.last_symbol,
                    is_keyword=True,
                    is_extra=True,
                ))
                cursor = new_cursor

            elif isinstance(cursor.last_symbol, parser_module.Characters['/']):
                if saw_end_position_only_marker:
                    raise parser_module.ParseError('multiple "end position-only" markers found', cursor)
                if saw_begin_keyword_only_marker:
                    raise parser_module.ParseError(
                        '"end position-only" marker found after "begin keyword-only" marker',
                        cursor,
                    )
                saw_end_position_only_marker = True

                # Rewrite all the previous arguments to position-only.
                for i, argument in enumerate(arguments):
                    if argument.is_extra:
                        continue  # Don't rewrite "extra" arguments.
                    arguments[i] = Argument(
                        variable=argument.variable,
                        is_positional=True,
                        is_keyword=False,
                        is_extra=False,
                    )

            elif new_cursor and isinstance(new_cursor.last_symbol, expression.Variable):
                arguments.append(Argument(
                    variable=new_cursor.last_symbol,
                    is_positional=not saw_begin_keyword_only_marker,
                    is_keyword=True,
                    is_extra=False,
                ))
                cursor = new_cursor

            else:
                break  # No more arguments to parse.

            cursor = cursor.parse_one_symbol([
                parser_module.Characters[','],
                parser_module.Always,
            ])

            if isinstance(cursor.last_symbol, parser_module.Always):
                break  # Additional arguments can only follow a comma, so we're done.

        return cursor.new_from_symbol(cls(
            arguments=arguments,
            cursor=cursor,
        ))


@attr.s(frozen=True, slots=True)
class Argument:
    """A function argument.
    """
    variable: expression.Variable = attr.ib()
    is_positional: bool = attr.ib(default=False)
    is_keyword: bool = attr.ib(default=False)
    is_extra: bool = attr.ib(default=False)


# pylint: disable=wrong-import-position
from . import expression  # noqa, handle import cycle
