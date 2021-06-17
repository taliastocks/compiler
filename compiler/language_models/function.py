from __future__ import annotations

import typing

import attr
import immutabledict

from . import statement, declarable, expression, argument_list, namespace as namespace_module
from ..libs import parser as parser_module

# pylint: disable=fixme
from ..meta import generic


@attr.s(frozen=True, slots=True)
class Function(declarable.Declarable, parser_module.Symbol):
    """A Function declaration and definition.
    """
    @attr.s(frozen=True, slots=True)
    class Decorator(parser_module.Symbol):
        value: expression.Expression = attr.ib()

        @classmethod
        def parse(cls, cursor):
            cursor = cursor.parse_one_symbol([
                parser_module.Characters['@']
            ])

            cursor = expression.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.EndLine
            ], fail=True)

            assert isinstance(cursor.last_symbol, expression.Expression)
            value = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.EndLine
            ], fail=True)

            return cursor.new_from_symbol(cls(
                cursor=cursor,
                value=value,
            ))

    body: statement.Block = attr.ib(factory=statement.Block, repr=False)

    bindings: argument_list.ArgumentList = attr.ib(factory=argument_list.ArgumentList, repr=False)
    arguments: argument_list.ArgumentList = attr.ib(factory=argument_list.ArgumentList, repr=False)
    decorators: typing.Sequence[Decorator] = attr.ib(converter=tuple, default=(), repr=False)
    return_type: typing.Optional[expression.Expression] = attr.ib(default=None, repr=False)

    locals: typing.Mapping[str, declarable.Declarable] = attr.ib(converter=immutabledict.immutabledict,
                                                                 init=False,
                                                                 repr=False)

    def execute(self, namespace: namespace_module.Namespace):
        @generic.Generic
        def bind_function(*binding_args, **binding_kwargs):
            binding_namespace = namespace_module.Namespace(namespace)
            self.bindings.unpack_values(binding_args, binding_kwargs, binding_namespace)

            def function_instance(*args, **kwargs):
                function_namespace = namespace_module.Namespace(binding_namespace)
                self.arguments.unpack_values(args, kwargs, function_namespace)
                return self.body.execute(function_namespace).get_value()

            return function_instance

        if self.bindings:
            function = bind_function
        else:
            function = bind_function[()]

        for decorator in reversed(self.decorators):
            with statement.Raise.Outcome.catch(decorator) as get_outcome:
                decorator_value: typing.Callable = decorator.value.execute(namespace).get_value()
                assert callable(decorator_value), 'decorator not callable'
                function = decorator_value(function)

            get_outcome().get_value()  # reraise any exception, with decorator added to traceback

        return function

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            Function.Decorator,
            parser_module.Characters['def'],
        ])

        decorators: list[Function.Decorator] = []
        while isinstance(cursor.last_symbol, Function.Decorator):
            assert isinstance(cursor.last_symbol, Function.Decorator)
            decorators.append(cursor.last_symbol)

            cursor = cursor.parse_one_symbol([
                Function.Decorator,
                parser_module.Characters['def'],
                parser_module.Characters['class'],
            ], fail=True)

            if isinstance(cursor.last_symbol, parser_module.Characters['class']):
                return None  # backtrack, parse class

        cursor = cursor.parse_one_symbol([
            parser_module.Identifier
        ], fail=True)

        assert isinstance(cursor.last_symbol, parser_module.Identifier)
        name = cursor.last_symbol.identifier

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['['],
            parser_module.Characters['('],
        ], fail=True)

        if isinstance(cursor.last_symbol, parser_module.Characters['[']):
            # parse bindings
            cursor = cursor.parse_one_symbol([
                argument_list.ArgumentList
            ], fail=True)

            assert isinstance(cursor.last_symbol, argument_list.ArgumentList)
            bindings = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.Characters[']'],
            ], fail=True).parse_one_symbol([
                parser_module.Characters['('],
            ], fail=True)
        else:
            bindings = argument_list.ArgumentList()

        cursor = cursor.parse_one_symbol([
            argument_list.ArgumentList
        ], fail=True)

        assert isinstance(cursor.last_symbol, argument_list.ArgumentList)
        arguments = cursor.last_symbol

        cursor = cursor.parse_one_symbol([
            parser_module.Characters[')'],
        ], fail=True)

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['->'],
            parser_module.Always,
        ])

        if isinstance(cursor.last_symbol, parser_module.Characters['->']):
            cursor = expression.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.Characters[':']
            ], fail=True)

            assert isinstance(cursor.last_symbol, expression.Expression)
            return_type = cursor.last_symbol
        else:
            return_type = None

        cursor = cursor.parse_one_symbol([
            parser_module.Characters[':']
        ], fail=True).parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            statement.Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, statement.Block)
        body = cursor.last_symbol

        return cursor.new_from_symbol(cls(
            cursor=cursor,
            name=name,
            bindings=bindings,
            arguments=arguments,
            decorators=decorators,
            return_type=return_type,
            body=body,
        ))

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
