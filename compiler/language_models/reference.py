import abc

import attr


@attr.s(frozen=True, slots=True)
class Reference(metaclass=abc.ABCMeta):
    """Represents a path, e.g. to a module or declaration.
    """
    name: str = attr.ib()


@attr.s(frozen=True, slots=True)
class ModuleReference(Reference):
    """Represents a reference to a module.
    """


@attr.s(frozen=True, slots=True)
class ClassReference(Reference):
    """Represents a reference to a class.
    """
