from __future__ import annotations

import abc
import typing


class Symbol(metaclass=abc.ABCMeta):
    pass


class Terminal(Symbol, metaclass=abc.ABCMeta):
    pass


class NonTerminal(Symbol, metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def production_rules(cls) -> typing.Iterable[typing.Sequence[typing.Type[Symbol]]]:
        pass


def repeated(symbol: typing.Type[Symbol]):
    class Repeated(NonTerminal):
        @classmethod
        def production_rules(cls):
            yield [symbol, cls]
            yield []  # Allow repetition to terminate.

    return Repeated


def sequence(*symbols: typing.Type[Symbol]):
    class Sequence(NonTerminal):
        @classmethod
        def production_rules(cls):
            yield symbols

    return Sequence


def one_of(*symbols: typing.Type[Symbol]):
    class OneOf(NonTerminal):
        @classmethod
        def production_rules(cls):
            yield from symbols

    return OneOf
