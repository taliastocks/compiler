from __future__ import annotations

import typing

import attr

from . import declarable, expression, argument_list, statement, namespace as namespace_module
from ..libs import parser as parser_module

# pylint: disable=fixme
from ..meta import generic


@attr.s(frozen=True, slots=True)
class Class(parser_module.Symbol, declarable.Declarable):
    """A Class declaration and definition.
    """
    @attr.s(frozen=True, slots=True)
    class Decorator(parser_module.Symbol):
        value: expression.Expression = attr.ib()

        @classmethod
        def parse(cls, cursor):
            cursor = cursor.parse_one_symbol([
                parser_module.Characters['@']
            ])

            expr_cursor = cursor = expression.ExpressionParser.parse(cursor, stop_symbols=[
                parser_module.EndLine
            ], fail=True)

            assert isinstance(cursor.last_symbol, expression.Expression)
            value = cursor.last_symbol

            cursor = cursor.parse_one_symbol([
                parser_module.EndLine
            ], fail=True)

            return cursor.new_from_symbol(cls(
                cursor=expr_cursor,
                value=value,
            ))

    body: statement.Block = attr.ib(factory=lambda: statement.Block(), repr=False)

    bindings: argument_list.ArgumentList = attr.ib(factory=argument_list.ArgumentList, repr=False)
    decorators: typing.Sequence[Decorator] = attr.ib(converter=tuple, default=(), repr=False)
    bases: typing.Sequence[expression.Expression] = attr.ib(converter=tuple, default=(), repr=False)

    def execute(self, namespace: namespace_module.Namespace):
        @generic.Generic
        def bind_class(*binding_args, **binding_kwargs):
            binding_namespace = namespace_module.Namespace(namespace)
            self.bindings.unpack_values(binding_args, binding_kwargs, binding_namespace)
            class_namespace = namespace_module.Namespace(binding_namespace)

            bases = []
            for base in self.bases:
                with statement.Raise.Outcome.catch(base) as get_outcome:
                    base_value = base.execute(binding_namespace)
                    assert isinstance(base_value, type), 'bases must be types'
                    bases.append(base_value)

                get_outcome().get_value()  # reraise any exception, with base expr added to traceback

            with statement.Raise.Outcome.catch(self.body) as get_outcome:
                self.body.execute(class_namespace).get_value()

            get_outcome().get_value()  # reraise any exception, with class body added to traceback

            with statement.Raise.Outcome.catch(self) as get_outcome:
                class_instance = type(self.name, tuple(bases), class_namespace.declarations)

            get_outcome().get_value()  # reraise any exception, with class added to traceback

            return class_instance

        if self.bindings:
            new_class = bind_class
        else:
            new_class = bind_class[()]

        for decorator in reversed(self.decorators):
            with statement.Raise.Outcome.catch(decorator) as get_outcome:
                decorator_value: typing.Callable = decorator.value.execute(namespace)
                assert callable(decorator_value), 'decorator not callable'
                new_class = decorator_value(new_class)

            get_outcome().get_value()  # reraise any exception, with decorator added to traceback

        namespace.declare(self.name, new_class)

    @classmethod
    def parse(cls, cursor):
        cursor = cursor.parse_one_symbol([
            Class.Decorator,
            parser_module.Characters['class'],
        ])

        decorators: list[Class.Decorator] = []
        while isinstance(cursor.last_symbol, Class.Decorator):
            assert isinstance(cursor.last_symbol, Class.Decorator)
            decorators.append(cursor.last_symbol)

            cursor = cursor.parse_one_symbol([
                Class.Decorator,
                parser_module.Characters['class'],
                parser_module.Characters['def'],
            ], fail=True)

            if isinstance(cursor.last_symbol, parser_module.Characters['def']):
                return None  # backtrack, parse function

        cursor = cursor.parse_one_symbol([
            parser_module.Identifier
        ], fail=True)

        assert isinstance(cursor.last_symbol, parser_module.Identifier)
        name = cursor.last_symbol.identifier

        cursor = cursor.parse_one_symbol([
            parser_module.Characters['['],
            parser_module.Characters['('],
            parser_module.Always,
        ])

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
                parser_module.Always,
            ])
        else:
            bindings = argument_list.ArgumentList()

        bases: list[expression.Expression] = []
        if isinstance(cursor.last_symbol, parser_module.Characters['(']):
            # parse parent classes
            while not isinstance(cursor.last_symbol, parser_module.Characters[')']):
                cursor = expression.ExpressionParser.parse(cursor, stop_symbols=[
                    parser_module.Characters[',']
                ]) or cursor

                if isinstance(cursor.last_symbol, expression.Expression):
                    bases.append(cursor.last_symbol)

                    cursor = cursor.parse_one_symbol([
                        parser_module.Characters[','],
                        parser_module.Characters[')'],
                    ], fail=True)
                else:
                    cursor = cursor.parse_one_symbol([
                        parser_module.Characters[')'],
                    ], fail=True)

        colon_cursor = cursor = cursor.parse_one_symbol([
            parser_module.Characters[':']
        ], fail=True)
        cursor = cursor.parse_one_symbol([
            parser_module.EndLine
        ], fail=True).parse_one_symbol([
            statement.Block
        ], fail=True)

        assert isinstance(cursor.last_symbol, statement.Block)
        body = cursor.last_symbol

        return cursor.new_from_symbol(cls(
            cursor=colon_cursor,
            name=name,
            bindings=bindings,
            decorators=decorators,
            bases=bases,
            body=body,
        ))
