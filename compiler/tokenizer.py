from __future__ import annotations

import abc
import typing

import attr

from . import grammar


@attr.s(frozen=True, slots=True)
class Tokenizer:
    buffer: str = attr.ib(repr=False)

    lines: typing.Sequence[str] = attr.ib(converter=tuple, init=False, repr=False)
    first_token: FirstToken = attr.ib(init=False, repr=False)

    def next(self, current_token: Token, one_of: typing.Sequence[typing.Type[Token]]) -> typing.Sequence[Token]:
        """Get the next token from the buffer.

        :param current_token: The current token being processed.
        :param one_of: The allowable token types for the next token.
        :return: All matching tokens.
        """

    @lines.default
    def _init_lines(self):
        return self.buffer.splitlines()

    @first_token.default
    def _init_first_token(self):
        return FirstToken(
            tokenizer=self,
            first_line=1,
            last_line=1,
            first_column=0,
            last_column=0,
        )


@attr.s(frozen=True, slots=True)
class Token(grammar.Terminal, metaclass=abc.ABCMeta):
    tokenizer: Tokenizer = attr.ib()
    first_line: int = attr.ib()
    last_line: int = attr.ib()
    first_column: int = attr.ib()
    last_column: int = attr.ib()

    def next(self, one_of: typing.Sequence[typing.Type[Token]]):
        """Get the next token from the buffer.

        :param one_of: The allowable token types for the next token.
        """
        return self.tokenizer.next(self, one_of)


@attr.s(frozen=True, slots=True)
class FirstToken(Token):
    pass
