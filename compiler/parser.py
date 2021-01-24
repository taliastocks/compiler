from __future__ import annotations

import abc
import typing

import attr
import regex

from .meta import generic


@attr.s(frozen=True)
class Parser(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def parse(cls, cursor: Cursor) -> typing.Optional[Cursor]:
        """Optionally parse a Symbol from a cursor.

        If a Symbol cannot be constructed from the cursor, returns None.
        """


@attr.s(frozen=True, slots=True)
class Cursor:
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
        """Get a new cursor from an existing cursor and a symbol.
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

        return Cursor(
            lines=self._lines,
            # Only allow one extra line (for cases where the file
            # doesn't end in a newline).
            line=min(line, self.last_line + 1),
            column=column,
            last_symbol=symbol,
            block_depth=block_depth,
        )

    def parse_one_symbol(self, one_of: typing.Sequence[typing.Type[Symbol]], fail=False) -> Cursor:
        """Parse one Symbol, returning a new Cursor object.

        Tries to parse the symbols in ``one_of`` in order, returning after the
        first success.

        :param one_of: Parse one of these Symbols.
        :param fail: Fail rather than backtracking if none of the symbols match.
        :return: A new Cursor object with ``cursor.last_symbol`` set.
        :raises NoMatchError: if none of the symbols match.
        """
        cursor = self
        for symbol_type in one_of:
            try:
                next_cursor = symbol_type.parse(cursor)
            except NoMatchError:
                continue
            else:
                if next_cursor is not None:
                    return next_cursor

        if fail:
            raise ParseError(
                message='expected one of ({})'.format(', '.join(symbol.symbol_name() for symbol in one_of)),
                cursor=cursor,
            )

        raise NoMatchError(
            message='none of the expected symbols were found',
            cursor=cursor,
            expected_symbols=one_of,
        )

    def __str__(self):
        heading = '{}, {}: '.format(self.line, self.column)
        line_text = self.line_text()
        pointer_indent = ' ' * (len(heading) + self.column)
        return '{}{}\n{}^'.format(heading, line_text, pointer_indent)


@attr.s(frozen=True, slots=True)
class ParseError(Exception):
    message: str = attr.ib()
    cursor: typing.Optional[Cursor] = attr.ib()

    def __str__(self):
        return '{}\n{}'.format(self.message, self.cursor)


@attr.s(frozen=True, slots=True)
class NoMatchError(ParseError):
    expected_symbols: typing.Sequence[typing.Type[Symbol]] = attr.ib()


@attr.s(frozen=True, slots=True)
class IndentationError(ParseError):  # noqa
    # pylint: disable=redefined-builtin
    line: int = attr.ib()
    column: int = attr.ib()


@attr.s
class Symbol(Parser, metaclass=abc.ABCMeta):
    cursor: typing.Optional[Cursor] = attr.ib(kw_only=True, repr=False, eq=False, default=None)

    @classmethod
    def symbol_name(cls):
        return cls.__name__


@attr.s(frozen=True, slots=True)
class Always(Symbol):
    """Always matches and consumes no characters.
    """
    @classmethod
    def parse(cls, cursor: Cursor):
        return cursor.new_from_symbol(cls())


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
    def parse(cls, cursor: Cursor):
        if cursor.line >= cursor.last_line:
            if cursor.column >= len(cursor.line_text()):
                # We parsed the whole line already.
                return cursor.new_from_symbol(cls(
                    first_line=cursor.line,
                    next_line=cursor.line,
                    first_column=cursor.column,
                    next_column=cursor.column,
                ))

        return None


@attr.s(frozen=True, slots=True)
class BlankLine(Token):
    """Token representing a blank line (or a line consisting only of spaces).
    """
    @classmethod
    def parse(cls, cursor: Cursor):
        if cursor.column != 0:
            return None  # Only match the beginning of a line.

        line = cursor.line_text()
        if not line or _WHITESPACE_REGEX.fullmatch(line):
            return cursor.new_from_symbol(cls(
                first_line=cursor.line,
                next_line=cursor.line + 1,
                first_column=0,
                next_column=0,
            ))

        return None


@attr.s(frozen=True, slots=True)
class EndLine(Token):
    """Token representing the end of a line.
    """
    @classmethod
    def parse(cls, cursor: Cursor):
        match = _END_LINE_REGEX.match(cursor.line_text()[cursor.column:])
        if match:
            return cursor.new_from_symbol(cls(
                first_line=cursor.line,
                next_line=cursor.line + 1,
                first_column=cursor.column,
                next_column=0,
            ))

        return None


@attr.s(frozen=True, slots=True)
class BeginBlock(Token):
    """Token representing the beginning of an indentation block.
    """
    block_depth: int = attr.ib()

    @classmethod
    def parse(cls, cursor: Cursor):
        if cursor.column != 0:
            return None  # Only match the beginning of a line.

        if cursor.block_depth < _measure_block_depth(cursor):
            return cursor.new_from_symbol(cls(
                first_line=cursor.line,
                next_line=cursor.line,
                first_column=cursor.column,
                next_column=cursor.column,
                # Block depth can only ever increase by one.
                block_depth=cursor.block_depth + 1,
            ))

        return None


@attr.s(frozen=True, slots=True)
class EndBlock(Token):
    """Token representing the end of an indentation block.
    """
    block_depth: int = attr.ib()

    @classmethod
    def parse(cls, cursor: Cursor):
        if cursor.column != 0:
            return None  # Only match the beginning of a line.

        if _measure_block_depth(cursor) < cursor.block_depth:
            return cursor.new_from_symbol(cls(
                first_line=cursor.line,
                next_line=cursor.line,
                first_column=cursor.column,
                next_column=cursor.column,
                # If the block depth decreased by more than one, we want
                # to produce one EndBlock token per block depth, so only
                # decrease the block depth by one at a time.
                block_depth=cursor.block_depth - 1,
            ))

        return None


@attr.s(frozen=True, slots=True)
class Whitespace(Token):
    """Token representing whitespace.
    """
    @classmethod
    def parse(cls, cursor: Cursor):
        match = _WHITESPACE_REGEX.match(cursor.line_text()[cursor.column:])

        if match:
            return cursor.new_from_symbol(cls(
                first_line=cursor.line,
                next_line=cursor.line,
                first_column=cursor.column,
                next_column=cursor.column + match.end(),
            ))

        return None


@attr.s(frozen=True, slots=True)
class MultilineWhitespace(Token):
    """Token representing whitespace, potentially split over multiple lines.
    """
    @classmethod
    def parse(cls, cursor: Cursor):
        match = _WHITESPACE_REGEX.match(cursor.line_text()[cursor.column:])
        next_line = cursor.line
        next_column = cursor.column

        if match:
            next_column += match.end()
            while True:
                if next_column == len(cursor.line_text(next_line)):
                    next_line += 1
                    match = _WHITESPACE_REGEX.match(cursor.line_text(next_line))
                    next_column = match.end()
                else:
                    return cursor.new_from_symbol(cls(
                        first_line=cursor.line,
                        next_line=next_line,
                        first_column=cursor.column,
                        next_column=next_column,
                    ))

        return None


@generic.Generic
def Regex(pattern):  # noqa
    # pylint: disable=invalid-name
    compiled_pattern = regex.compile(r'^ *({})(?:$|\b|(?=\W))'.format(pattern), regex.V1)

    @attr.s(frozen=True, slots=True)
    class Regex(Token):  # noqa
        # pylint: disable=redefined-outer-name
        groups: typing.Sequence[typing.Optional[str]] = attr.ib(converter=tuple, default=())

        @classmethod
        def symbol_name(cls):
            return '{}[{!r}]'.format(cls.__name__, pattern)

        @classmethod
        def parse(cls, cursor: Cursor):
            while True:  # Eat newlines.
                new_cursor = cursor.parse_one_symbol([EndLine, Always])
                if new_cursor.line == cursor.line:
                    break
                cursor = new_cursor

            match = compiled_pattern.match(cursor.line_text()[cursor.column:])

            if match:
                return cursor.new_from_symbol(cls(
                    first_line=cursor.line,
                    next_line=cursor.line,
                    first_column=cursor.column + match.start(1),
                    next_column=cursor.column + match.end(1),
                    groups=match.groups(),
                ))

            return None

    return Regex


@generic.Generic
def Characters(characters):  # noqa
    # pylint: disable=invalid-name

    @attr.s(frozen=True, slots=True, repr=False)
    class Characters(Regex[regex.escape(characters)]):  # noqa
        # pylint: disable=redefined-outer-name
        @classmethod
        def symbol_name(cls):
            return repr(characters)

    return Characters


@attr.s(frozen=True, slots=True)
class Identifier(Regex[r'[\w--\d]\w*']):
    """Token representing a valid variable name or reserved word.

    An identifier must be a non-digit word character followed by zero or more
    word characters.
    """
    @property
    def identifier(self):
        return self.groups[0]


def _measure_block_depth(cursor):
    """Measure the block depth for the current line number.

    Indentation must be a multiple of four spaces. If

    :raises IndentationError: on bad indentation
    """
    match = _INDENT_REGEX.match(cursor.line_text())

    if match.group(2):  # group(2) matches tabs
        raise IndentationError(
            cursor=cursor,
            message='each block must be indented four spaces (other whitespace found)',
            line=cursor.line,
            column=match.start(2),  # first other space character
        )

    indentation = match.end()
    block_depth, remainder = divmod(indentation, 4)

    if remainder:
        raise IndentationError(
            cursor=cursor,
            message='each block must be indented four spaces (extra spaces found)',
            line=cursor.line,
            column=block_depth * 4,  # start of extra spaces
        )

    if cursor.block_depth + 1 < block_depth:
        raise IndentationError(
            cursor=cursor,
            message='each block must be indented four spaces (block over-indented)',
            line=cursor.line,
            column=(cursor.block_depth + 1) * 4,  # start of extra indentation
        )

    return block_depth


_END_LINE_REGEX = regex.compile(r'^ *$')
_INDENT_REGEX = regex.compile(r'^( *)(\s*)')
_WHITESPACE_REGEX = regex.compile(r'^\s+')
