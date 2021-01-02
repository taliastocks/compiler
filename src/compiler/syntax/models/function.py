from __future__ import annotations

import enum
import typing

import attr

from . import statement as statement_module, namespace, variable, expression


@attr.s(frozen=True, slots=True)
class Function(namespace.Declarable):
    """A Function declaration and definition.
    """
    # pylint: disable=too-many-instance-attributes
    @attr.s(frozen=True, slots=True)
    class Argument:
        variable: expression.Variable = attr.ib()
        is_positional: bool = attr.ib(default=False)
        is_keyword: bool = attr.ib(default=False)
        is_extra: bool = attr.ib(default=False)

        @is_keyword.validator
        def _check_is_keyword_or_is_positional(self, _, is_keyword):
            """All arguments must be positional or keyword or both.
            """
            if not self.is_positional and not is_keyword:
                raise ValueError('all arguments must be positional or keyword or both')

        @is_extra.validator
        def _check_is_extra(self, _, is_extra):
            """Extra arguments cannot be both positional and keyword.
            """
            if self.is_positional and self.is_keyword and is_extra:
                raise ValueError('"extra" arguments cannot be both positional and keyword')

    @attr.s(frozen=True, slots=True)
    class Decorator:
        pass

    body: statement_module.Block = attr.ib(factory=statement_module.Block, repr=False)
    is_async: bool = attr.ib(default=False, repr=False)

    arguments: typing.Sequence[Argument] = attr.ib(converter=tuple, default=(), repr=False)
    decorators: typing.Sequence[Decorator] = attr.ib(converter=tuple, default=(), repr=False)

    is_generator: bool = attr.ib(init=False, repr=False)
    local_scope: namespace.FunctionNamespace = attr.ib(init=False, repr=False)

    class _ArgumentPrecedence(enum.IntEnum):
        positional_only = 1
        positional_keyword = 2
        positional_extra = 3
        keyword_only = 4
        keyword_extra = 5

        @classmethod
        def from_argument(cls, argument: Function.Argument):
            try:
                return {
                    (True, False, False): cls.positional_only,
                    (True, True, False): cls.positional_keyword,
                    (True, False, True): cls.positional_extra,
                    (False, True, False): cls.keyword_only,
                    (False, True, True): cls.keyword_extra,
                }[argument.is_positional, argument.is_keyword, argument.is_extra]
            except KeyError as exc:
                raise RuntimeError('this should be unreachable') from exc

    @arguments.validator
    def _check_arguments(self, _, arguments: typing.Sequence[Argument]):
        """Check that arguments appear in a meaningful order: zero or more positional-
        only arguments, followed by zero or more position+keyword arguments, followed
        by zero or one "extra positionals" argument, followed by zero or more keyword-
        only arguments, followed by zero or one "extra keywords" argument.
        """
        argument_precedences = [
            Function._ArgumentPrecedence.from_argument(arg)
            for arg in arguments
        ]

        last_precedence = Function._ArgumentPrecedence.positional_only
        for argument, precedence in zip(arguments, argument_precedences):
            if precedence < last_precedence:
                raise ValueError('{!r}: {} argument may not appear after {} argument'.format(
                    argument.variable.name,
                    precedence.name,
                    last_precedence.name,
                ))

            if precedence == last_precedence and argument.is_extra:
                raise ValueError('{!r}: cannot have multiple {} arguments'.format(
                    argument.variable.name,
                    precedence.name,
                ))

            last_precedence = precedence

    @is_generator.default
    def _init_is_generator(self):
        """A function which yields is a generator.
        """
        return self.body.has_yield

    @local_scope.default
    def _init_local_scope(self):
        local_scope = namespace.FunctionNamespace(
            name='{}.{}'.format(self.namespace.name, self.name) if self.namespace is not None else '',
            parent=self.namespace,
        )

        for argument in self.arguments:
            try:
                local_scope.declare(
                    variable.Variable(
                        name=argument.variable.name,
                        annotations=argument.variable.annotations,
                        namespace=local_scope,
                    )
                )
            except KeyError as exc:
                raise ValueError('{!r}: repeated argument name not allowed'.format(
                    argument.variable.name
                )) from exc

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
            local_scope.declare(
                variable.Variable(
                    name=local_name,
                    namespace=local_scope,
                )
            )

        return local_scope