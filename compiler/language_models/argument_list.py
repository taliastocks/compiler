from __future__ import annotations

import collections
import typing

import attr

from . import namespace as namespace_module, exceptions
from ..libs import parser as parser_module


@attr.s(frozen=True, slots=True)
class ArgumentList(parser_module.Symbol):
    """A list of function arguments.
    """
    arguments: typing.Sequence[Argument] = attr.ib(converter=tuple, default=())

    def unpack_values(self,
                      positional_values: typing.Sequence[typing.Any],
                      keyword_values: typing.Mapping[str, typing.Any],
                      namespace: namespace_module.Namespace):
        # pylint: disable=too-many-branches

        # Copy arguments to prevent mutation.
        positional_values = collections.deque(positional_values)
        keyword_values = dict(keyword_values)
        no_value = object()
        expected_positionals = 0

        for argument in self.arguments:
            value = no_value

            if argument.is_positional:
                if argument.is_extra:
                    # Consume all remaining positional values.
                    value = list(positional_values)
                    positional_values.clear()
                else:
                    expected_positionals += 1
                    try:
                        value = positional_values.popleft()
                    except IndexError:
                        pass

            if argument.is_keyword:
                if argument.is_extra:
                    # Consume all remaining keyword values.
                    value = dict(keyword_values)
                    keyword_values.clear()
                else:
                    try:
                        value = keyword_values.pop(argument.variable.name)
                    except KeyError:
                        pass

            if value is no_value:
                if argument.variable.initializer is not None:
                    value = argument.variable.initializer.execute(namespace)
                else:
                    raise exceptions.TypeError(f'no value for parameter {argument.variable.name!r}')

            namespace.declare(argument.variable.name, value)

        if positional_values:
            raise exceptions.TypeError(f'too many positional arguments: '
                                       f'expected {expected_positionals}, '
                                       f'got {expected_positionals + len(positional_values)}')
        if keyword_values:
            raise exceptions.TypeError(f'unexpected keyword argument(s): {", ".join(keyword_values.keys())}')

    def __iter__(self):
        return iter(self.arguments)

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

    @arguments.validator
    def _check_arguments(self, _, arguments: typing.Sequence[Argument]):
        has_extra_positionals = False
        has_extra_keywords = False

        for argument in arguments:
            if argument.is_extra:
                if argument.is_positional:
                    if has_extra_positionals:
                        raise exceptions.ValueError('multiple "extra positional" arguments not allowed')
                    has_extra_positionals = True
                if argument.is_keyword:
                    if has_extra_keywords:
                        raise exceptions.ValueError('multiple "extra keyword" arguments not allowed')
                    has_extra_keywords = True


@attr.s(frozen=True, slots=True)
class Argument:
    """A function argument.
    """
    variable: expression.Variable = attr.ib()
    is_positional: bool = attr.ib(default=False)
    is_keyword: bool = attr.ib(default=False)
    is_extra: bool = attr.ib(default=False)

    @is_keyword.validator
    def _check_is_keyword(self, _, is_keyword):
        if not is_keyword and not self.is_positional:
            raise exceptions.ValueError('all arguments must be positional or keyword or both')

    @is_extra.validator
    def _check_is_extra(self, _, is_extra):
        if is_extra:
            if self.is_positional and self.is_keyword:
                raise exceptions.ValueError('"extra" arguments cannot be both positional and keyword')


# pylint: disable=wrong-import-position, cyclic-import
from . import expression  # noqa, handle import cycle
