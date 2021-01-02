from __future__ import annotations

import collections
import typing

import attr

from ...meta import instance_cache


@attr.s(frozen=True, slots=True)
class ProgramPartBase(metaclass=instance_cache.InstanceCacheABCMeta):
    """Represents part of a C program.
    """
    indent = '  '
    suggested_line_length = 100
    class_dependencies = ()  # All instances of these classes are considered dependencies.

    @property
    def dependencies(self) -> typing.Generator[ProgramPartBase, None, None]:
        """Yield all the direct dependencies.
        """
        yield from []

    def render_program_part(self) -> typing.Generator[_NestedStrings, None, None]:
        """Render the program part as a sequence of strings (one per line).
        """
        yield from []


@attr.s(frozen=True, slots=True)
class Program:
    """Represents a program.
    """
    _parts_by_class: typing.DefaultDict[type, typing.Dict[ProgramPartBase, None]] = attr.ib(
        factory=lambda: collections.defaultdict(dict),  # dict reproduces insertion order on iteration
        init=False,
    )

    def add(self, program_part: ProgramPartBase):
        for dependency in program_part.dependencies:
            if dependency not in self._parts_by_class[type(program_part)]:
                self.add(dependency)

        self._parts_by_class[type(program_part)][program_part] = None

    def __iter__(self) -> typing.Generator[str, None, None]:
        """Iterator to render the program line by line.
        """
        for program_part in self.program_parts:
            for line in program_part.render_program_part():
                yield ''.join(_flatten(line))

    @property
    def program_parts(self):
        """Iterator over all the program parts in order of dependencies.
        """
        visited = set()  # Halt depth-first search if we hit a part we've already returned.
        ancestors = set()  # Detect dependency cycles.

        def sort_program_parts(program_parts):
            """Topological sort based on Depth-First Search.
            """
            for program_part in program_parts:
                if program_part not in visited:
                    if program_part in ancestors:
                        raise RuntimeError('cycle detected in dependency graph')

                    ancestors.add(program_part)
                    # Expand class dependencies to all instances of that class and recursively sort.
                    for class_dependency in program_part.class_dependencies:
                        yield from sort_program_parts(self._parts_by_class[class_dependency])
                    # Recursively sort instance dependencies.
                    yield from sort_program_parts(program_part.dependencies)
                    ancestors.remove(program_part)

                    visited.add(program_part)
                    yield program_part

        for part_class in self._parts_by_class.keys():
            yield from sort_program_parts(self._parts_by_class[part_class])


_NestedStrings = typing.Union[str, typing.Sequence['_NestedStrings']]


def _flatten(nested_strings: _NestedStrings) -> typing.Generator[str, None, None]:
    """Flatten a nested tuple of strings into a tuple of strings.
    """
    if isinstance(nested_strings, str):
        yield nested_strings
    else:
        for item in nested_strings:
            yield from _flatten(item)
