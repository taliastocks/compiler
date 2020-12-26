import typing

import attr

from . import statement, namespace as namespace_module, variable


@attr.s(frozen=True, slots=True)
class Function(namespace_module.Declarable):
    """A Function declaration and definition.
    """

    @attr.s(frozen=True, slots=True)
    class Argument:
        name: str

    body: statement.Block
    is_async: bool = attr.ib(default=False)
    is_generator: bool = attr.ib(default=False)

    positional_arguments: typing.Sequence[Argument] = attr.ib(converter=tuple, default=())
    keyword_arguments: typing.Collection[Argument] = attr.ib(converter=frozenset, default=())
    extra_positional_arguments: typing.Optional[Argument] = attr.ib(default=None)
    extra_keyword_arguments: typing.Optional[Argument] = attr.ib(default=None)

    namespace: namespace_module.FunctionNamespace = attr.ib(factory=namespace_module.FunctionNamespace, init=False)

    @namespace.validator
    def _register_arguments(self, _, namespace: namespace_module.FunctionNamespace):
        # Gather all arguments in a set, since arguments may be appear in both positional
        # and keyword arguments.
        all_arguments = set(self.positional_arguments) | set(self.keyword_arguments)

        if self.extra_positional_arguments is not None:
            all_arguments.add(self.extra_positional_arguments)
        if self.extra_keyword_arguments is not None:
            all_arguments.add(self.extra_keyword_arguments)

        for argument in all_arguments:
            variable.Variable(
                name=argument.name,
                namespace=namespace,
            )
