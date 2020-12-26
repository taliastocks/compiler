from __future__ import annotations

import abc

import attr


@attr.s(frozen=True, slots=True)
class Declarable(metaclass=abc.ABCMeta):
    """A Declarable is an object such as a function or a variable
    which can be declared within a namespace.
    """

    name: str
    namespace: Namespace = attr.ib()

    @namespace.validator
    def _register_with_namespace(self, _, namespace: Namespace):
        namespace.register(self)


@attr.s(frozen=True, slots=True)
class Namespace(metaclass=abc.ABCMeta):
    """A Namespace (or scope) is an environment to hold a logical
    grouping of identifiers or symbols.
    """

    def register(self, declarable: Declarable):
        pass


@attr.s(frozen=True, slots=True)
class FunctionNamespace(Namespace):
    pass
