from __future__ import annotations

import abc
import threading
import typing

import attr


@attr.s(slots=True)
class Namespace:
    """Represents a global namespace.
    """
    _name: typing.Optional[str] = attr.ib(
        default=None,
        init=False,
        validator=attr.validators.optional(attr.validators.instance_of(str))
    )
    _parent: typing.Optional[Namespace] = attr.ib(default=None, init=False)
    _declaration: DeclarationBase = attr.ib(default=None, init=False)
    _lock: threading.RLock = attr.ib(factory=threading.RLock, init=False)
    _members: typing.MutableMapping[str, Namespace] = attr.ib(factory=dict, init=False)

    @property
    def name(self) -> str:
        """Get the name of this namespace.
        """
        return self._name

    @property
    def path(self) -> typing.Generator[str, None, None]:
        """Get the full path of this namespace.
        """
        if self._parent is not None:
            yield from self._parent.path
        if self._name:
            yield self._name

    @property
    def parent(self) -> typing.Optional[Namespace]:
        """Get the parent of this namespace.
        """
        return self._parent

    @property
    def members(self) -> typing.Generator[Namespace, None, None]:
        """Get the sub-namespaces in this namespace.
        """
        yield from self._members.values()

    @property
    def declaration(self) -> typing.Optional[DeclarationBase]:
        """Get the declaration at this path, if any.
        """
        return self._declaration

    @declaration.setter
    def declaration(self, declaration: DeclarationBase) -> None:
        """Assign a declaration to exist at this namespace path.
        """
        with self._lock:
            if self._declaration is not None:
                raise ValueError('{} already declared'.format(list(self.path)))
            if declaration.namespace is not self._parent:
                raise ValueError('declaration.namespace must be the parent namespace')
            if declaration.name != self._name:
                raise ValueError('declaration.name must match this namespace')
            self._declaration = declaration

    def resolve(self, name: str) -> Namespace:
        """Resolve a namespace by name. The namespace is either a child of the
        current namespace, or a child of one of its ancestors. A new namespace
        is never implicitly created.
        """
        with self._lock:
            if name in self._members:
                return self._members[name]
            if self._parent is not None:
                return self._parent.resolve(name)
            raise KeyError(name)

    def __getitem__(self, name: str) -> Namespace:
        """Get a child namespace by name. Creates a new one if one doesn't exist.
        """
        with self._lock:
            if name not in self._members:
                self._members[name] = child = Namespace()
                child._name = name
                child._parent = self
            return self._members[name]


@attr.s(frozen=True, slots=True)
class DeclarationBase(metaclass=abc.ABCMeta):
    name: str = attr.ib(validator=attr.validators.instance_of(str))
    namespace: Namespace = attr.ib(
        validator=lambda inst, attr_, value: attr.validators.instance_of(Namespace)(inst, attr_, value)
    )

    @namespace.validator
    def _attach_to_namespace(self, _, namespace):
        namespace[self.name].declaration = self


@attr.s(frozen=True, slots=True)
class Global(DeclarationBase):
    pass


@attr.s(frozen=True, slots=True)
class Function(DeclarationBase):
    pass


@attr.s(frozen=True, slots=True)
class Class(DeclarationBase):
    @attr.s(frozen=True, slots=True)
    class Method:
        pass

    @attr.s(frozen=True, slots=True)
    class Attribute:
        pass

    bases: typing.Collection[Class] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=lambda inst, attr_, value: attr.validators.instance_of(Class)(inst, attr_, value),
            iterable_validator=attr.validators.instance_of(frozenset),
        ),
        converter=frozenset,
    )
    attributes: typing.Collection[Attribute] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Method),
            iterable_validator=attr.validators.instance_of(frozenset),
        ),
        converter=frozenset,
    )
    methods: typing.Collection[Method] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Method),
            iterable_validator=attr.validators.instance_of(frozenset),
        ),
        converter=frozenset,
    )
