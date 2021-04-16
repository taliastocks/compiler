import unittest

from . import class_, expression, argument_list, statement
from ..lib import parser as parser_module


class ClassTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            class_.Class.parse(
                parser_module.Cursor([
                    '@decorator_1',
                    '@decorator_2',
                    'class MyClass[a](b):',
                    '    body',
                ])
            ).last_symbol,
            class_.Class(
                name='MyClass',
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                bindings=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('a'),
                        is_positional=True,
                        is_keyword=True,
                    )
                ]),
                bases=[
                    expression.Variable('b'),
                ],
                decorators=[
                    class_.Class.Decorator(
                        expression.Variable('decorator_1')
                    ),
                    class_.Class.Decorator(
                        expression.Variable('decorator_2')
                    ),
                ],
            )
        )

        # Bindings are optional.
        self.assertEqual(
            class_.Class.parse(
                parser_module.Cursor([
                    '@decorator_1',
                    '@decorator_2',
                    'class MyClass(b):',
                    '    body',
                ])
            ).last_symbol,
            class_.Class(
                name='MyClass',
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                bindings=argument_list.ArgumentList(),
                bases=[
                    expression.Variable('b'),
                ],
                decorators=[
                    class_.Class.Decorator(
                        expression.Variable('decorator_1')
                    ),
                    class_.Class.Decorator(
                        expression.Variable('decorator_2')
                    ),
                ],
            )
        )

        # Bases are optional.
        self.assertEqual(
            class_.Class.parse(
                parser_module.Cursor([
                    '@decorator_1',
                    '@decorator_2',
                    'class MyClass[a]:',
                    '    body',
                ])
            ).last_symbol,
            class_.Class(
                name='MyClass',
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                bindings=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('a'),
                        is_positional=True,
                        is_keyword=True,
                    )
                ]),
                bases=[],
                decorators=[
                    class_.Class.Decorator(
                        expression.Variable('decorator_1')
                    ),
                    class_.Class.Decorator(
                        expression.Variable('decorator_2')
                    ),
                ],
            )
        )

        # Decorators are optional.
        self.assertEqual(
            class_.Class.parse(
                parser_module.Cursor([
                    'class MyClass[a](b):',
                    '    body',
                ])
            ).last_symbol,
            class_.Class(
                name='MyClass',
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                bindings=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('a'),
                        is_positional=True,
                        is_keyword=True,
                    )
                ]),
                bases=[
                    expression.Variable('b'),
                ],
                decorators=[],
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            class_.Class.parse(
                parser_module.Cursor([
                    '@'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    '@decorator a'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Decorator, \'class\', \'def\'\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    '@decorator'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Identifier\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    '@decorator',
                    'class',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    'class foo',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\']\'\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    'class foo[',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\':\'\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    'class foo[]',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'\)\'\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    'class foo[](',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'\:\'\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    'class foo()',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    'class foo(): foo',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            class_.Class.parse(
                parser_module.Cursor([
                    'class foo():',
                ])
            )


class ClassDecoratorTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            class_.Class.Decorator.parse(
                parser_module.Cursor([
                    '@foo',
                    'next line',
                ])
            ).last_symbol,
            class_.Class.Decorator(
                value=expression.Variable('foo')
            )
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            class_.Class.Decorator.parse(
                parser_module.Cursor([
                    '@foo bar'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            class_.Class.Decorator.parse(
                parser_module.Cursor([
                    '@'
                ])
            )
