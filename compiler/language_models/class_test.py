import unittest
from unittest import mock

from . import class_, expression, argument_list, statement, namespace as namespace_module
from ..libs import parser as parser_module


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

    def test_execute(self):
        test_class: class_.Class = class_.Class.parse(  # noqa
            parser_module.Cursor([
                'class Accumulator:',
                '    sum: int = 0',
                '    def add(self, additional):',
                '        self.sum = self.sum + additional',
            ])
        ).last_symbol

        namespace = namespace_module.Namespace()
        test_class.execute(namespace)
        Accumulator = namespace.lookup('Accumulator')  # noqa, pylint: disable=invalid-name

        accumulator = Accumulator()
        self.assertEqual(0, accumulator.sum)

        accumulator.add(3)
        self.assertEqual(3, accumulator.sum)

        accumulator.add(10)
        self.assertEqual(13, accumulator.sum)

    def test_execute_multiple_instances(self):
        test_class: class_.Class = class_.Class.parse(  # noqa
            parser_module.Cursor([
                'class Accumulator:',
                '    sum: int = 0',
                '    def add(self, additional):',
                '        self.sum = self.sum + additional',
            ])
        ).last_symbol

        namespace = namespace_module.Namespace()
        test_class.execute(namespace)
        Accumulator = namespace.lookup('Accumulator')  # noqa, pylint: disable=invalid-name

        accumulator_1 = Accumulator()
        accumulator_2 = Accumulator()

        accumulator_1.add(3)
        accumulator_2.add(5)

        self.assertEqual(3, accumulator_1.sum)
        self.assertEqual(5, accumulator_2.sum)

    def test_execute_generic(self):
        test_class: class_.Class = class_.Class.parse(  # noqa
            parser_module.Cursor([
                'class Accumulator[start]:',
                '    sum: int = start',
                '    def add(self, additional):',
                '        self.sum = self.sum + additional',
            ])
        ).last_symbol

        namespace = namespace_module.Namespace()
        test_class.execute(namespace)
        Accumulator = namespace.lookup('Accumulator')  # noqa, pylint: disable=invalid-name

        accumulator = Accumulator[5]()
        self.assertEqual(5, accumulator.sum)

        accumulator.add(2)
        self.assertEqual(7, accumulator.sum)

    def test_execute_constructor(self):
        test_class: class_.Class = class_.Class.parse(  # noqa
            parser_module.Cursor([
                'class Accumulator:',
                '    sum: int = 0',
                '    def add(self, additional):',
                '        self.sum = self.sum + additional',
            ])
        ).last_symbol

        namespace = namespace_module.Namespace()
        test_class.execute(namespace)
        Accumulator = namespace.lookup('Accumulator')  # noqa, pylint: disable=invalid-name

        accumulator = Accumulator(sum=5)
        self.assertEqual(5, accumulator.sum)

        accumulator.add(2)
        self.assertEqual(7, accumulator.sum)

    def test_execute_extra_kwargs(self):
        test_class: class_.Class = class_.Class.parse(  # noqa
            parser_module.Cursor([
                'class Accumulator:',
                '    sum: int = 0',
                '    def add(self, additional):',
                '        self.sum = self.sum + additional',
            ])
        ).last_symbol

        namespace = namespace_module.Namespace()
        test_class.execute(namespace)
        Accumulator = namespace.lookup('Accumulator')  # noqa, pylint: disable=invalid-name

        with self.assertRaisesRegex(TypeError, r'unexpected keyword argument\(s\): a, b'):
            Accumulator(a=1, b=2)

    def test_execute_decorator(self):
        test_class: class_.Class = class_.Class.parse(  # noqa
            parser_module.Cursor([
                '@my_decorator',
                'class Accumulator:',
                '    sum: int = 0',
                '    def add(self, additional):',
                '        self.sum = self.sum + additional',
            ])
        ).last_symbol

        my_decorator = mock.Mock()

        namespace = namespace_module.Namespace()
        namespace.declare('my_decorator', my_decorator)
        test_class.execute(namespace)
        Accumulator = namespace.lookup('Accumulator')  # noqa, pylint: disable=invalid-name

        OriginalAccumulator = my_decorator.call_args[0][0]  # noqa, pylint: disable=invalid-name
        accumulator = OriginalAccumulator(sum=4)
        accumulator.add(2)
        self.assertEqual(6, accumulator.sum)

        self.assertIsInstance(Accumulator, mock.Mock)

    def test_execute_inheritance(self):
        test_class: class_.Class = class_.Class.parse(  # noqa
            parser_module.Cursor([
                'class Accumulator(MyBase):',
                '    sum: int = 0',
                '    def add(self, additional):',
                '        self.sum = self.sum + additional',
            ])
        ).last_symbol

        class MyBase:
            sum = None

            def get_sum(self):
                return self.sum

        namespace = namespace_module.Namespace()
        namespace.declare('MyBase', MyBase)
        test_class.execute(namespace)
        Accumulator = namespace.lookup('Accumulator')  # noqa, pylint: disable=invalid-name

        accumulator = Accumulator(sum=3)
        self.assertIsInstance(accumulator, Accumulator)
        self.assertIsInstance(accumulator, MyBase)

        self.assertEqual(3, accumulator.get_sum())

    # TODO: test exceptions in decorators, class body, methods, etc


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
