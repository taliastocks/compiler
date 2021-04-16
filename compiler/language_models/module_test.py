import textwrap
import unittest

from . import module, function, class_, expression, statement
from ..libs import parser as parser_module


class ModuleTestCase(unittest.TestCase):
    def test_from_string(self):
        self.assertEqual(
            module.Module.from_string(textwrap.dedent(
                '''\
                import foo

                def bar():
                    hello
                '''
            )),
            module.Module([
                statement.Declaration(
                    statement.Import('foo', ['foo'])
                ),
                statement.Declaration(
                    function.Function(
                        name='bar',
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('hello')
                            )
                        ]),
                    )
                ),
            ])
        )

    def test_parse(self):
        self.assertEqual(
            module.Module.parse(
                parser_module.Cursor([
                    'import foo',
                    'def bar():',
                    '    hello',
                ])
            ).last_symbol,
            module.Module([
                statement.Declaration(
                    statement.Import('foo', ['foo'])
                ),
                statement.Declaration(
                    function.Function(
                        name='bar',
                        body=statement.Block([
                            statement.Declaration(
                                expression.Variable('hello')
                            )
                        ]),
                    )
                ),
            ])
        )

    def test_init_globals(self):
        my_module = module.Module(
            statements=[
                statement.Declaration(
                    statement.Import('foo', ['foo'])
                ),
                statement.Declaration(
                    function.Function('bar')
                ),
                statement.Declaration(
                    class_.Class('Baz')
                ),
                statement.Declaration(
                    expression.Variable('bip')
                ),
            ],
        )

        self.assertEqual(
            {
                'foo': statement.Import('foo', ['foo']),
                'bar': function.Function('bar'),
                'Baz': class_.Class('Baz'),
                'bip': expression.Variable('bip'),
            },
            my_module.globals
        )

        with self.assertRaisesRegex(ValueError, r"Variable\(name='foo'\) cannot be declared with the same "
                                                r"name as Function\(name='foo'\)"):
            module.Module(
                statements=[
                    statement.Declaration(
                        function.Function('foo')
                    ),
                    statement.Declaration(
                        expression.Variable('foo')
                    ),
                ],
            )
