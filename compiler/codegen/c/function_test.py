import unittest

from . import function, types, statement
from .types import integer


class FunctionTestCase(unittest.TestCase):
    def test_pointer_type(self):
        my_func = function.Function(
            name='my_function',
            arguments=[
                function.Function.Argument('foo', integer.Int(signed=False)),
                function.Function.Argument('bar', integer.LongLong().pointer),
            ],
            return_type=types.Void(),
            statements=[],
        )

        self.assertEqual(
            types.FunctionPointer(
                argument_types=[
                    integer.Int(signed=False),
                    integer.LongLong().pointer
                ],
                return_type=types.Void(),
            ),
            my_func.pointer_type
        )

    def test_dependencies(self):
        my_func = function.Function(
            name='my_function',
            arguments=[
                function.Function.Argument('foo', integer.Int(signed=False)),
                function.Function.Argument('bar', integer.LongLong().pointer),
            ],
            return_type=types.Void(),
            statements=[
                statement.ReturnStatement()
            ],
        )

        self.assertEqual(
            [
                function.Function.ForwardDeclaration(
                    name='my_function',
                    argument_types=[
                        integer.Int(signed=False),
                        integer.LongLong().pointer,
                    ],
                    return_type=types.Void(),
                ),
                statement.ReturnStatement(),
            ],
            list(my_func.dependencies)
        )

        self.assertEqual(
            [
                integer.Int(signed=False),
                integer.LongLong().pointer,
                types.Void(),
            ],
            list(my_func.forward_declaration.dependencies)
        )

    def test_forward_declaration(self):
        my_func = function.Function(
            name='my_function',
            arguments=[
                function.Function.Argument('foo', integer.Int(signed=False)),
                function.Function.Argument('bar', integer.LongLong().pointer),
            ],
            return_type=types.Void(),
            statements=[
                statement.ReturnStatement()
            ],
        )

        self.assertEqual(
            function.Function.ForwardDeclaration(
                name='my_function',
                argument_types=[
                    integer.Int(signed=False),
                    integer.LongLong().pointer,
                ],
                return_type=types.Void(),
            ),
            my_func.forward_declaration
        )

    def test_render_program_part(self):
        my_func = function.Function(
            name='my_function',
            arguments=[
                function.Function.Argument('foo', integer.Int(signed=False)),
                function.Function.Argument('bar', integer.LongLong().pointer),
            ],
            return_type=types.Void(),
            statements=[
                statement.ReturnStatement()
            ],
        )

        self.assertEqual(
            [
                'void my_function(',
                ('  ', 'unsigned_int', ' ', 'foo', ','),
                ('  ', '_long_long_Ptr', ' ', 'bar'),
                ') {',
                ('  ', 'return;'),
                '}',
            ],
            list(my_func.render_program_part())
        )
