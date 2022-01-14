from __future__ import annotations

import pathlib
import typing

import attr

from . import module as module_module


@attr.s(frozen=True, slots=True)
class Program:
    modules: dict[typing.Sequence[str], typing.Union[module_module.Module, bytes]] = attr.ib(factory=dict, init=False)
    initialized_modules: dict[typing.Sequence[str], namespace_module.Namespace.Object] = \
        attr.ib(factory=dict, init=False)

    def register_module(self, path: typing.Sequence[str], module: module_module.Module):
        self.modules[tuple(path)] = module

    def register_module_from_string(self, path: typing.Sequence[str], module_string: str):
        self.register_module(
            path,
            module_module.Module.from_string(module_string),
        )

    def register_package(self, path: typing.Sequence[str], root_path: str):
        path = tuple(path)
        for file_path in pathlib.Path(root_path).glob('**/*'):
            if file_path.is_file():
                if file_path.suffix == '.sib':
                    sib_path = path + file_path.relative_to(root_path).with_suffix('').parts
                    print(f'Compiling "{file_path.absolute()}"')
                    self.register_module_from_string(sib_path, file_path.read_text())

                self.modules[
                    path + file_path.relative_to(root_path).parts
                ] = file_path.read_bytes()

    def get_module(self, path: typing.Sequence[str]):
        path = tuple(path)

        if path not in self.initialized_modules:
            if path not in self.modules:
                raise ImportError(f'no such module {path}')

            self.initialized_modules[path] = self.modules[path].execute(self, path)

        return self.initialized_modules[path]


from . import namespace as namespace_module  # noqa, pylint: disable=cyclic-import, wrong-import-position
