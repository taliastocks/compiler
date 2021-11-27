import textwrap
import unittest

from . import module, function, expression, statement
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

    def test_execute(self):
        my_module = module.Module.from_string(textwrap.dedent(
            '''\
            def foo():
                return 'bar'

            def add(a, b):
                return a + b
            '''
        )).execute()

        self.assertEqual(
            'bar',
            my_module.foo()  # noqa
        )

        self.assertEqual(
            7,
            my_module.add(3, 4)
        )
