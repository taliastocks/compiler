from __future__ import annotations

import os
import typing

import attr

from .language_models import module


@attr.s(slots=True)
class Program:
    modules: typing.MutableMapping = attr.ib(init=False, factory=dict)

    def load_module(self, name: str, code: str):
        """Load a module from source code.
        """
        self.modules[name] = module.Module.from_string(code)

    def load_directory(self, package: str, base_path: str):
        """Load a package from a directory.
        """
        for dirpath, _, filenames in os.walk(base_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                file_relative_path = os.path.relpath(file_path, base_path)
                module_path, ext = os.path.splitext(file_relative_path)
                module_name = '.'.join(os.path.split(module_path)).lstrip('.')

                if ext.lower() != '.sib':
                    continue

                with open(file_path, encoding='utf-8') as file:
                    self.load_module(package + '.' + module_name, file.read())
