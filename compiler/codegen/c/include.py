from __future__ import annotations

import attr

from . import program


@attr.s(frozen=True, slots=True)
class Include(program.ProgramPartBase):
    """Represents an "include" directive.
    """
    path = attr.ib(type=str, validator=attr.validators.instance_of(str))
    builtin = attr.ib(type=bool, validator=attr.validators.instance_of(bool))

    def render_program_part(self):
        if self.builtin:
            yield f'#include <{self.path}>'
        else:
            yield f'#include "{self.path}"'
