from __future__ import annotations

import enum
import typing

import attr
import immutabledict

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

    body: statement_module.Block = attr.ib(factory=statement_module.Block, repr=False)
    is_async: bool = attr.ib(default=False, repr=False)

    arguments: typing.Sequence[Argument] = attr.ib(converter=tuple, default=(), repr=False)

    positional_arguments: typing.Sequence[Argument] = attr.ib(converter=tuple, init=False, repr=False)
    keyword_arguments: typing.Mapping[str, Argument] = attr.ib(converter=immutabledict.immutabledict,
                                                               init=False,
                                                               repr=False)
    extra_positionals_argument: typing.Optional[Argument] = attr.ib(init=False, repr=False)
    extra_keywords_argument: typing.Optional[Argument] = attr.ib(init=False, repr=False)
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

    @positional_arguments.default
    def _init_positional_arguments(self):
        """Extract the positional arguments to a convenience attribute.
        """
        for argument in self.arguments:
            if argument.is_positional and not argument.is_extra:
                yield argument

    @keyword_arguments.default
    def _init_keyword_arguments(self):
        """Extract the keyword arguments to a convenience attribute.
        """
        for argument in self.arguments:
            if argument.is_keyword and not argument.is_extra:
                yield argument.variable.name, argument

    @extra_positionals_argument.default
    def _init_extra_positionals_argument(self):
        """If an argument is supplied to hold extra positional arguments, find it.
        """
        for argument in self.arguments:
            if argument.is_positional and argument.is_extra:
                return argument
        return None

    @extra_keywords_argument.default
    def _init_extra_keywords_argument(self):
        """If an argument is supplied to hold extra keyword arguments, find it.
        """
        for argument in self.arguments:
            if argument.is_keyword and argument.is_extra:
                return argument
        return None

    @is_generator.default
    def _init_is_generator(self):
        """A function which yields is a generator.
        """
        return self.body.has_yield

    @local_scope.default
    def _init_local_scope(self):
        local_scope = namespace.FunctionNamespace(
            name='{}.{}'.format(self.namespace.name, self.name),
            parent=self.namespace,
        )

        for argument in self.arguments:
            try:
                local_scope.declare(
                    variable.Variable(
                        name=argument.variable.name,
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
        assigned_variable_names = {
            assigned_variable.name for assigned_variable in self.body.variable_assignments
        }
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
