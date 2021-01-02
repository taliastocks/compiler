import typing

import attr


@attr.s(frozen=True, slots=True)
class Path:
    """Represents a path, e.g. to a module or declaration.
    """
    name: str = attr.ib()
    path: typing.Sequence[str] = attr.ib(converter=tuple, init=False, repr=False)

    @path.default
    def _init_path(self):
        return self.name.split('.')


@attr.s(frozen=True, slots=True)
class ModulePath(Path):
    """Represents the path to a module.
    """


@attr.s(frozen=True, slots=True)
class ClassPath(Path):
    """Represents the path to a class.
    """
