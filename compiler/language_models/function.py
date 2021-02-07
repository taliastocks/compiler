from __future__ import annotations

import typing

import attr
import immutabledict

from . import statement, declarable, expression, argument_list
from .. import parser as parser_module


@attr.s(frozen=True, slots=True)
class Function(declarable.Declarable, parser_module.Symbol):
    """A Function declaration and definition.
    """
    @attr.s(frozen=True, slots=True)
    class Decorator:
        pass

    body: statement.Block = attr.ib(factory=statement.Block, repr=False)
    is_async: bool = attr.ib(default=False, repr=False)

    arguments: argument_list.ArgumentList = attr.ib(factory=argument_list.ArgumentList, repr=False)
    decorators: typing.Sequence[Decorator] = attr.ib(converter=tuple, default=(), repr=False)

    is_generator: bool = attr.ib(init=False, repr=False)
    locals: typing.Mapping[declarable.Declarable] = attr.ib(converter=immutabledict.immutabledict,
                                                            init=False,
                                                            repr=False)

    @classmethod
    def parse(cls, cursor):
        pass  # Placeholder until I get around to writing a real implementation.

    @is_generator.default
    def _init_is_generator(self):
        """A function which yields is a generator.
        """
        return self.body.has_yield

    @locals.default
    def _init_locals(self):
        local_declarations = {}

        for argument in self.arguments:
            if argument.variable.name in local_declarations:
                raise ValueError('{!r}: repeated argument name not allowed'.format(
                    argument.variable.name
                ))

            var = expression.Variable(
                name=argument.variable.name,
                annotation=argument.variable.annotation,
            )
            local_declarations[var.name] = var

        # Find all the variable assignments from the function body,
        # as well as all the "nonlocal" declarations.
        argument_names = {
            argument.variable.name for argument in self.arguments
        }
        nonlocal_variable_names = {
            nonlocal_variable.name for nonlocal_variable in self.body.nonlocal_variables
        }
        assigned_variables_by_names: dict[str, expression.Variable] = {
            assigned_variable.name: assigned_variable
            for assigned_variable in self.body.variable_assignments
        }
        assigned_variable_names = set(assigned_variables_by_names.keys())
        local_variable_names = assigned_variable_names - nonlocal_variable_names

        argument_names_declared_nonlocal = argument_names & nonlocal_variable_names
        if argument_names_declared_nonlocal:
            raise ValueError('arguments cannot be declared nonlocal: {}'.format(
                ', '.join(sorted(argument_names_declared_nonlocal))
            ))

        # Declare all the local variables (anything assigned and not declared nonlocal),
        # but skip arguments (which were already declared above).
        for local_name in local_variable_names - argument_names:
            local_declarations[local_name] = expression.Variable(name=local_name)

        return local_declarations
