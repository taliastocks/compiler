import abc

import attr

from .. import parser as parser_module


@attr.s(frozen=True, slots=True)
class Reference(parser_module.Symbol, metaclass=abc.ABCMeta):
    """Represents a path, e.g. to a module or declaration.
    """
    name: str = attr.ib()


@attr.s(frozen=True, slots=True)
class ModuleReference(Reference):
    """Represents a reference to a module.
    """

    @classmethod
    def parse(cls, cursor):
        pass
