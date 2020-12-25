import typing

import attr

from . import value, operation


@attr.s(frozen=True, slots=True)
class Operation:
    pass


@attr.s(frozen=True, slots=True)
class Function:
    inputs: typing.Sequence[value.Value] = attr.ib(factory=tuple, converter=tuple)
    outputs: typing.Sequence[value.Value] = attr.ib(factory=tuple, converter=tuple)
    body: operation.Operation = attr.ib(factory=operation.Operation)


@attr.s(frozen=True, slots=True)
class FunctionBuilder:
    _inputs: typing.MutableSequence[value.Value] = attr.ib(factory=list, init=False)
    _locals: typing.MutableMapping[str, value.Value] = attr.ib(factory=dict, init=False)
    _operations: typing.MutableSequence[Operation] = attr.ib(factory=list, init=False)
    _output: value.Value = attr.ib(factory=value.Value)

    def declare_input(self, name: str):
        argument = self.declare_local(name)
        self._inputs.append(argument)
        return argument

    def declare_local(self, name: str):
        if name in self._locals:
            raise ValueError('local already defined: {}'.format(name))

        self._locals[name] = local = value.Value(name=name)
        return local

    def get_local(self, name: str):
        return self._locals[name]

    def build(self):
        pass
