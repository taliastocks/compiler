from __future__ import annotations

import abc
import typing

import attr


@attr.s(frozen=True, slots=True)
class Declarable(metaclass=abc.ABCMeta):
    """A Declarable is an object such as a function or a variable
    which can be declared within a namespace.
    """

    name: str = attr.ib()
    namespace: Namespace = attr.ib()


@attr.s(frozen=True, slots=True)
class Namespace(metaclass=abc.ABCMeta):
    """A Namespace (or scope) is an environment to hold a logical
    grouping of identifiers or symbols.

    TODO: tests
    """
    name: str = attr.ib()
    parent: typing.Optional[Namespace] = attr.ib(default=None, repr=False)
    declarations: typing.MutableMapping[str, Declarable] = attr.ib(factory=dict, init=False, repr=False)

    def declare(self, declarable: Declarable):
        if declarable.name in self.declarations:
            raise KeyError('{!r} already declared in namespace {!r}'.format(
                declarable.name,
                self,
            ))
        if declarable.namespace is not self:
            raise ValueError('expected {!r}.namespace to be {!r}, but got {!r}'.format(
                declarable,
                self,
                declarable.namespace,
            ))

        self.declarations[declarable.name] = declarable

    def get(self, name: str):
        return self.declarations.get(name)

    def lookup(self, name: str):
        declarable = self.get(name)
        if declarable is None and self.parent is not None:
            return self.parent.lookup(name)
        return declarable


@attr.s(frozen=True, slots=True)
class FunctionNamespace(Namespace):
    """Represents the inner scope of a function.
    """
