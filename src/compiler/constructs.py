from __future__ import annotations

import abc
import threading
import typing

import attr


@attr.s(slots=True)
class Namespace(object):
    """Represents a global namespace.
    """
    _name: typing.Optional[str] = attr.ib(
        default=None,
        validator=attr.validators.optional(
            attr.validators.and_(
                attr.validators.instance_of(str),
                attr.validators.matches_re(r'^\w+$'),  # Any word characters are allowed,
                attr.validators.matches_re(r'^\D'),  # except the first character must not be a digit.
            )
        )
    )
    _parent: typing.Optional[Namespace] = attr.ib(default=None)
    _declaration: ConstructBase = attr.ib(default=None, init=False)
    _lock: threading.RLock = attr.ib(factory=threading.RLock, init=False)
    _members: typing.MutableMapping[str, Namespace] = attr.ib(factory=dict, init=False)

    @property
    def path(self) -> str:
        if self._parent is not None:
            return '.'.join([self._parent.path, self._name])
        return self._name

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> Namespace:
        return self._parent

    def declare(self, construct: ConstructBase) -> None:
        """Declare a construct to exist at this namespace path.
        """
        with self._lock:
            if self._declaration is not None:
                raise ValueError('{} already declared'.format(self.path))
            self._declaration = construct

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
            raise KeyError('no such name {!r} in namespace {}'.format(name, self.path))

    def get(self, name: str) -> Namespace:
        """Get a child namespace by name. Creates a new one if one doesn't exist.
        """
        with self._lock:
            if name not in self._members:
                self._members[name] = Namespace(name, self)
            return self._members[name]


@attr.s(frozen=True, slots=True)
class ConstructBase(object, metaclass=abc.ABCMeta):
    name: str = attr.ib(validator=attr.validators.instance_of(str))
    namespace: Namespace = attr.ib(
        validator=lambda inst, attr_, value: attr.validators.instance_of(Namespace)(inst, attr_, value)
    )

    @namespace.validator
    def _declare_with_namespace(self, _, namespace):
        """Declare this construct in the given namespace, or fail.
        """
        namespace.register(self)


@attr.s(frozen=True, slots=True)
class Class(ConstructBase):
    @attr.s(frozen=True, slots=True)
    class Method(ConstructBase):
        pass

    @attr.s(frozen=True, slots=True)
    class Attribute(ConstructBase):
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
