from __future__ import annotations

import typing

import attr

from . import declarable, expression, argument_list, statement
from ..libs import parser as parser_module

# pylint: disable=fixme


@attr.s(frozen=True, slots=True)
class Class(parser_module.Symbol, declarable.Declarable):
    """A Class declaration and definition.
    """
    @attr.s(frozen=True, slots=True)
    class Decorator(parser_module.Symbol):
        value: expression.Expression = attr.ib()

        @classmethod
        def parse(cls, cursor):
            cursor = cursor.parse_one_symbol([
                parser_module.Characters['@']
            ])

            cursor = expression.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.EndLine
            ], fail=True)

            assert isinstance(cursor.last_symbol, expression.Expression)
            value = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.EndLine
            ], fail=True)

            return cursor.new_from_symbol(cls(
                cursor=cursor,
                value=value,
            ))

    body: statement.Block = attr.ib(factory=lambda: statement.Block(), repr=False)

    bindings: argument_list.ArgumentList = attr.ib(factory=argument_list.ArgumentList, repr=False)
    decorators: typing.Sequence[Decorator] = attr.ib(converter=tuple, default=(), repr=False)
    bases: typing.Sequence[expression.Expression] = attr.ib(converter=tuple, default=(), repr=False)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            Class.Decorator,
            parser_module.Characters['class'],
        ])

        decorators: list[Class.Decorator] = []
        while isinstance(cursor.last_symbol, Class.Decorator):
            assert isinstance(cursor.last_symbol, Class.Decorator)
            decorators.append(cursor.last_symbol)

            cursor = cursor.parse_one_symbol([
                Class.Decorator,
                parser_module.Characters['class'],
                parser_module.Characters['def'],
            ], fail=True)

            if isinstance(cursor.last_symbol, parser_module.Characters['def']):
                return None  # backtrack, parse function

        cursor = cursor.parse_one_symbol([
            parser_module.Identifier
        ], fail=True)

        assert isinstance(cursor.last_symbol, parser_module.Identifier)
        name = cursor.last_symbol.identifier

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['['],
            parser_module.Characters['('],
            parser_module.Always,
        ])

        if isinstance(cursor.last_symbol, parser_module.Characters['[']):
            # parse bindings
            cursor = cursor.parse_one_symbol([
                argument_list.ArgumentList
            ], fail=True)

            assert isinstance(cursor.last_symbol, argument_list.ArgumentList)
            bindings = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.Characters[']'],
            ], fail=True).parse_one_symbol([
                parser_module.Characters['('],
                parser_module.Always,
            ])
        else:
            bindings = argument_list.ArgumentList()

        bases: list[expression.Expression] = []
        if isinstance(cursor.last_symbol, parser_module.Characters['(']):
            # parse parent classes
            while not isinstance(cursor.last_symbol, parser_module.Characters[')']):
                cursor = expression.ExpressionParser.parse(cursor, stop_symbols=[
                    parser_module.Characters[',']
                ]) or cursor

                if isinstance(cursor.last_symbol, expression.Expression):
                    bases.append(cursor.last_symbol)

                    cursor = cursor.parse_one_symbol([
                        parser_module.Characters[','],
                        parser_module.Characters[')'],
                    ], fail=True)
                else:
                    cursor = cursor.parse_one_symbol([
                        parser_module.Characters[')'],
                    ], fail=True)

        colon_cursor = cursor = cursor.parse_one_symbol([
            parser_module.Characters[':']
        ], fail=True)
        cursor = cursor.parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            statement.Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, statement.Block)
        body = cursor.last_symbol

        return cursor.new_from_symbol(cls(
            cursor=colon_cursor,
            name=name,
            bindings=bindings,
            decorators=decorators,
            bases=bases,
            body=body,
        ))
