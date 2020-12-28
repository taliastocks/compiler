import typing

import attr

from . import expression, statement as statement_module, namespace, variable


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
        nonlocal_names = set()
        assigned_variables = set()

        statement: statement_module.Statement
        for statement in self.body.linearize():
            if isinstance(statement, statement_module.Nonlocal):
                statement: statement_module.Nonlocal
                nonlocal_names.update(
                    var.name for var in statement.variables
                )

            if isinstance(statement, statement_module.ReceiverStatement):
                receiver: expression.LValue
                for receiver in statement.receivers:
                    if isinstance(receiver, expression.Variable):
                        assigned_variables.add(receiver.name)
                    if isinstance(receiver, expression.Unpack):
                        assigned_variables.update(
                            var.name for var in receiver.variables
                        )

        # Declare all the local variables (anything assigned and not declared nonlocal).
        for local_name in assigned_variables - nonlocal_names:
            local_scope.declare(
                variable.Variable(
                    name=local_name,
                    namespace=local_scope,
                )
            )

        return local_scope
