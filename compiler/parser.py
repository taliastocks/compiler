from __future__ import annotations

import abc
import typing

import attr


@attr.s(frozen=True, slots=True)
class Parser:
    lines: typing.Sequence[str] = attr.ib(converter=tuple, repr=False)
    line: int = attr.ib(default=0)
    column: int = attr.ib(default=0)
    last_symbol: typing.Optional[Symbol] = attr.ib(default=None)

    def new_from_symbol(self, symbol: Symbol):
        """Get a new parser from an existing parser and a symbol.
        """
        if isinstance(symbol, Token):
            line = symbol.next_line
            column = symbol.next_column
        else:
            line = self.line
            column = self.column

        return Parser(
            lines=self.lines,
            line=line,
            column=column,
            last_symbol=symbol,
        )

    def parse(self, one_of: typing.Sequence[typing.Type[Symbol]]) -> Parser:
        """Parse one Symbol, returning a new Parser object.

        Tries to parse the symbols in ``one_of`` in order, returning after the
        first success.

        :param one_of: Parse one of these Symbols.
        :return: A new Parser object with ``parser.last_symbol`` set.
        :raises ParseError: if none of the symbols can be parsed.
        """
        for symbol_type in one_of:
            next_parser = symbol_type.parse(self)
            if next_parser is not None:
                return next_parser

        raise ParseError(
            parser=self,
            expected=one_of,
        )


@attr.s(frozen=True, slots=True)
class ParseError(Exception):
    parser: Parser = attr.ib()
    expected: typing.Sequence[typing.Type[Symbol]] = attr.ib()

    def __str__(self):
        return 'expected one of ({})'.format(
            ', '.join(
                symbol_class.__qualname__
                for symbol_class in self.expected
            )
        )


class Symbol(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def parse(cls, parser: Parser) -> typing.Optional[Parser]:
        """Construct this Symbol from a Parser.

        If this Symbol cannot be constructed from the parser, returns None.
        """


@attr.s(frozen=True, slots=True)
class Token(Symbol, metaclass=abc.ABCMeta):
    first_line: int = attr.ib()
    next_line: int = attr.ib()
    first_column: int = attr.ib()
    next_column: int = attr.ib()


@attr.s(frozen=True, slots=True)
class EndFile(Token):
    """Token representing the end of a file.
    """
    @classmethod
    def parse(cls, parser: Parser):
        if parser.line < len(parser.lines) - 1:
            return None
        if parser.line == len(parser.lines) - 1:
            line = parser.lines[parser.line]
            if parser.column < len(line):
                return None

        return parser.new_from_symbol(cls(
            first_line=parser.line,
            next_line=parser.line,
            first_column=parser.column,
            next_column=parser.column,
        ))
