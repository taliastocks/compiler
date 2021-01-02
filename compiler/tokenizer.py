from __future__ import annotations

import typing

import attr


@attr.s(frozen=True, slots=True)
class Tokenizer:
    buffer: str = attr.ib(repr=False)
    lines: typing.Sequence[str] = attr.ib(converter=tuple, init=False, repr=False)

    def next(self, current_token: Token, one_of: typing.Sequence[typing.Type[Token]]):
        """Get the next token from the buffer.

        :param current_token: The current token being processed.
        :param one_of: The allowable token types for the next token.
        """

    @lines.default
    def _init_lines(self):
        return self.buffer.splitlines()


@attr.s(frozen=True, slots=True)
class Token:
    tokenizer: Tokenizer = attr.ib()
    line: int = attr.ib()
    column: int = attr.ib()
    value: str = attr.ib()

    def next(self, one_of: typing.Sequence[typing.Type[Token]]):
        """Get the next token from the buffer.

        :param one_of: The allowable token types for the next token.
        """
        return self.tokenizer.next(self, one_of)
