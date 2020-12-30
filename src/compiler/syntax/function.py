import typing

import attr

from . import statement as statement_module, namespace, variable


@attr.s(frozen=True, slots=True)
class Function(namespace.Declarable):
    """A Function declaration and definition.

    TODO: tests
    """
    # pylint: disable=too-many-instance-attributes

    @attr.s(frozen=True, slots=True)
    class Argument:
        name: str = attr.ib()

    body: statement_module.Block = attr.ib()
    is_async: bool = attr.ib(default=False)
    is_generator: bool = attr.ib(default=False)

    positional_arguments: typing.Sequence[Argument] = attr.ib(converter=tuple, default=())
    keyword_arguments: typing.Collection[Argument] = attr.ib(converter=frozenset, default=())
    extra_positional_arguments: typing.Optional[Argument] = attr.ib(default=None)
    extra_keyword_arguments: typing.Optional[Argument] = attr.ib(default=None)

    local_scope: namespace.FunctionNamespace = attr.ib(init=False)

    @is_generator.validator
    def _check_is_generator(self, _, is_generator):
        if is_generator is False and self.body.has_yield:
            raise ValueError('body of non-generator contains ``yield`` expression')

    @local_scope.default
    def _init_local_scope(self):
        local_scope = namespace.FunctionNamespace(
            name='{}.{}'.format(self.namespace.name, self.name),
            parent=self.namespace,
        )

        # Gather all arguments in a set, since arguments may be appear in both positional
        # and keyword arguments.
        all_arguments = set(self.positional_arguments) | set(self.keyword_arguments)

        if self.extra_positional_arguments is not None:
            all_arguments.add(self.extra_positional_arguments)
        if self.extra_keyword_arguments is not None:
            all_arguments.add(self.extra_keyword_arguments)

        for argument in all_arguments:
            local_scope.declare(
                variable.Variable(
                    name=argument.name,
                    namespace=local_scope,
                )
            )

        # Find all the variable assignments from the function body,
        # as well as all the "nonlocal" declarations.
        nonlocal_names = {
            nonlocal_variable.name for nonlocal_variable in self.body.nonlocal_variables
        }
        assigned_variable_names = {
            assigned_variable.name for assigned_variable in self.body.variable_assignments
        }

        # Declare all the local variables (anything assigned and not declared nonlocal).
        for local_name in assigned_variable_names - nonlocal_names:
            local_scope.declare(
                variable.Variable(
                    name=local_name,
                    namespace=local_scope,
                )
            )

        return local_scope
