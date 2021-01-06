from __future__ import annotations

import abc
import typing

import attr
import regex

from .meta import generic


@attr.s(frozen=True, slots=True)
class Parser:
    _lines: typing.Sequence[str] = attr.ib(converter=tuple, repr=False)
    line: int = attr.ib(default=0)
    column: int = attr.ib(default=0)
    last_symbol: typing.Optional[Symbol] = attr.ib(default=None)
    block_depth: int = attr.ib(default=0)

    def line_text(self, line=None):
        line = self.line if line is None else line
        if line < len(self._lines):
            return self._lines[line]
        return ''

    @property
    def last_line(self):
        return max(0, len(self._lines) - 1)

    def new_from_symbol(self, symbol: Symbol):
        """Get a new parser from an existing parser and a symbol.
        """
        if isinstance(symbol, (BeginBlock, EndBlock)):
            block_depth = symbol.block_depth
        else:
            block_depth = self.block_depth

        if isinstance(symbol, Token):
            line = symbol.next_line
            column = symbol.next_column
        else:
            line = self.line
            column = self.column

        return Parser(
            lines=self._lines,
            # Only allow one extra line (for cases where the file
            # doesn't end in a newline).
            line=min(line, self.last_line + 1),
            column=column,
            last_symbol=symbol,
            block_depth=block_depth,
        )

    def parse(self, one_of: typing.Sequence[typing.Type[Symbol]]) -> Parser:
        """Parse one Symbol, returning a new Parser object.

        Tries to parse the symbols in ``one_of`` in order, returning after the
        first success.

        :param one_of: Parse one of these Symbols.
        :return: A new Parser object with ``parser.last_symbol`` set.
        :raises NoMatchError: if none of the symbols match.
        """
        for i, symbol_type in enumerate(one_of):
            try:
                next_parser = symbol_type.parse(self)
            except NoMatchError as exc:
                if i == len(one_of) - 1:
                    raise NoMatchError(
                        message='none of the expected symbols were found',
                        parser=self,
                        expected_symbols=one_of,
                    ) from exc
            else:
                if next_parser is not None:
                    return next_parser

        raise NoMatchError(
            message='none of the expected symbols were found',
            parser=self,
            expected_symbols=one_of,
        )


@attr.s(frozen=True, slots=True)
class ParseError(Exception):
    message: str = attr.ib()
    parser: Parser = attr.ib()

    def __str__(self):
        return self.message


@attr.s(frozen=True, slots=True)
class NoMatchError(ParseError):
    expected_symbols: typing.Sequence[typing.Type[Symbol]] = attr.ib()


@attr.s(frozen=True, slots=True)
class IndentationError(ParseError):  # noqa
    # pylint: disable=redefined-builtin
    line: int = attr.ib()
    column: int = attr.ib()


class Symbol(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def parse(cls, parser: Parser) -> typing.Optional[Parser]:
        """Construct this Symbol from a Parser.

        If this Symbol cannot be constructed from the parser, returns None.
        """


@attr.s(frozen=True, slots=True)
class Always(Symbol):
    """Always matches and consumes no characters.
    """
    @classmethod
    def parse(cls, parser: Parser):
        return parser.new_from_symbol(cls())


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
        if parser.line >= parser.last_line:
            if parser.column >= len(parser.line_text()):
                # We parsed the whole line already.
                return parser.new_from_symbol(cls(
                    first_line=parser.line,
                    next_line=parser.line,
                    first_column=parser.column,
                    next_column=parser.column,
                ))

        return None


@attr.s(frozen=True, slots=True)
class BlankLine(Token):
    """Token representing a blank line (or a line consisting only of spaces).
    """
    @classmethod
    def parse(cls, parser: Parser):
        if parser.column != 0:
            return None  # Only match the beginning of a line.

        line = parser.line_text()
        if not line or _WHITESPACE_REGEX.fullmatch(line):
            return parser.new_from_symbol(cls(
                first_line=parser.line,
                next_line=parser.line + 1,
                first_column=0,
                next_column=0,
            ))

        return None


@attr.s(frozen=True, slots=True)
class EndLine(Token):
    """Token representing the end of a line.
    """
    @classmethod
    def parse(cls, parser: Parser):
        match = _END_LINE_REGEX.match(parser.line_text()[parser.column:])
        if match:
            return parser.new_from_symbol(cls(
                first_line=parser.line,
                next_line=parser.line + 1,
                first_column=parser.column,
                next_column=0,
            ))

        return None


@attr.s(frozen=True, slots=True)
class BeginBlock(Token):
    """Token representing the beginning of an indentation block.
    """
    block_depth: int = attr.ib()

    @classmethod
    def parse(cls, parser: Parser):
        if parser.column != 0:
            return None  # Only match the beginning of a line.

        if parser.block_depth < _measure_block_depth(parser):
            return parser.new_from_symbol(cls(
                first_line=parser.line,
                next_line=parser.line,
                first_column=parser.column,
                next_column=parser.column,
                # Block depth can only ever increase by one.
                block_depth=parser.block_depth + 1,
            ))

        return None


@attr.s(frozen=True, slots=True)
class EndBlock(Token):
    """Token representing the end of an indentation block.
    """
    block_depth: int = attr.ib()

    @classmethod
    def parse(cls, parser: Parser):
        if parser.column != 0:
            return None  # Only match the beginning of a line.

        if _measure_block_depth(parser) < parser.block_depth:
            return parser.new_from_symbol(cls(
                first_line=parser.line,
                next_line=parser.line,
                first_column=parser.column,
                next_column=parser.column,
                # If the block depth decreased by more than one, we want
                # to produce one EndBlock token per block depth, so only
                # decrease the block depth by one at a time.
                block_depth=parser.block_depth - 1,
            ))

        return None


@attr.s(frozen=True, slots=True)
class Whitespace(Token):
    """Token representing whitespace.
    """
    @classmethod
    def parse(cls, parser: Parser):
        match = _WHITESPACE_REGEX.match(parser.line_text()[parser.column:])

        if match:
            return parser.new_from_symbol(cls(
                first_line=parser.line,
                next_line=parser.line,
                first_column=parser.column,
                next_column=parser.column + match.end(),
            ))

        return None


@attr.s(frozen=True, slots=True)
class MultilineWhitespace(Token):
    """Token representing whitespace, potentially split over multiple lines.
    """
    @classmethod
    def parse(cls, parser: Parser):
        match = _WHITESPACE_REGEX.match(parser.line_text()[parser.column:])
        next_line = parser.line
        next_column = parser.column

        if match:
            next_column += match.end()
            while True:
                if next_column == len(parser.line_text(next_line)):
                    next_line += 1
                    match = _WHITESPACE_REGEX.match(parser.line_text(next_line))
                    next_column = match.end()
                else:
                    return parser.new_from_symbol(cls(
                        first_line=parser.line,
                        next_line=next_line,
                        first_column=parser.column,
                        next_column=next_column,
                    ))

        return None


@attr.s(frozen=True, slots=True)
class Identifier(Token):
    """Token representing a valid variable name or reserved word.

    An identifier must be a non-digit word character followed by zero or more
    word characters.
    """
    identifier: str = attr.ib()

    @classmethod
    def parse(cls, parser: Parser):
        match = _IDENTIFIER_REGEX.match(parser.line_text()[parser.column:])

        if match:
            return parser.new_from_symbol(cls(
                first_line=parser.line,
                next_line=parser.line,
                first_column=parser.column,
                next_column=parser.column + match.end(),
                identifier=match.group(1),
            ))

        return None


@generic.Generic
def Characters(characters):  # noqa
    # pylint: disable=invalid-name
    characters_regex = regex.compile(r'^ *({})'.format(regex.escape(characters)))

    class Characters(Token):  # noqa
        # pylint: disable=redefined-outer-name
        @classmethod
        def parse(cls, parser: Parser):
            match = characters_regex.match(parser.line_text()[parser.column:])

            if match:
                return parser.new_from_symbol(cls(
                    first_line=parser.line,
                    next_line=parser.line,
                    first_column=parser.column,
                    next_column=parser.column + match.end(),
                ))

            return None

    return Characters


def _measure_block_depth(parser):
    """Measure the block depth for the current line number.

    Indentation must be a multiple of four spaces. If

    :raises IndentationError: on bad indentation
    """
    match = _INDENT_REGEX.match(parser.line_text())

    if match.group(2):  # group(2) matches tabs
        raise IndentationError(
            parser=parser,
            message='each block must be indented four spaces (other whitespace found)',
            line=parser.line,
            column=match.start(2),  # first other space character
        )

    indentation = match.end()
    block_depth, remainder = divmod(indentation, 4)

    if remainder:
        raise IndentationError(
            parser=parser,
            message='each block must be indented four spaces (extra spaces found)',
            line=parser.line,
            column=block_depth * 4,  # start of extra spaces
        )

    if parser.block_depth + 1 < block_depth:
        raise IndentationError(
            parser=parser,
            message='each block must be indented four spaces (block over-indented)',
            line=parser.line,
            column=(parser.block_depth + 1) * 4,  # start of extra indentation
        )

    return block_depth


_END_LINE_REGEX = regex.compile(r'^ *$')
_INDENT_REGEX = regex.compile(r'^( *)(\s*)')
_WHITESPACE_REGEX = regex.compile(r'^\s+')
_IDENTIFIER_REGEX = regex.compile(r'^ *([\w--\d]\w*)', regex.V1)
