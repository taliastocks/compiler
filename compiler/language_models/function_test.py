import unittest

from . import function, expression, statement, argument_list, namespace as namespace_module
from ..libs import parser as parser_module


class FunctionTestCase(unittest.TestCase):
    def test_execute_basic(self):
        test_function: function.Function = function.Function.parse(  # noqa
            parser_module.Cursor([
                'def add_a(b):',
                '    return A + b',
            ])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('A', 3)
        test_function.execute(namespace)

        add_a = namespace.lookup('add_a')
        self.assertTrue(callable(add_a))
        self.assertEqual(
            7,
            add_a(4)  # 3 + 4 = 7
        )
        self.assertEqual(
            9,
            add_a(b=6)  # 3 + 4 = 9
        )

    def test_execute_exception(self):
        test_function: function.Function = function.Function.parse(  # noqa
            parser_module.Cursor([
                'def test_function():',
                '    test_function_2()',
            ])
        ).last_symbol
        test_function_2: function.Function = function.Function.parse(  # noqa
            parser_module.Cursor([
                'def test_function_2():',
                '    raise RuntimeError("hello world")',
            ])
        ).last_symbol

        namespace = namespace_module.Namespace()
        namespace.declare('RuntimeError', RuntimeError)
        test_function.execute(namespace)
        test_function_2.execute(namespace)

        with statement.Raise.Outcome.catch(test_function) as get_outcome:
            namespace.lookup('test_function')()

        outcome = get_outcome()

        self.assertEqual(
            '\n'.join([
                '0, 20: def test_function():',
                '                           ^',
                '1, 21:     test_function_2()',
                '                            ^',
                '1, 37:     raise RuntimeError("hello world")',
                '                                            ^',
                "RuntimeError('hello world')",
            ]),
            str(outcome)
        )

    def test_execute_generic(self):
        test_function: function.Function = function.Function.parse(  # noqa
            parser_module.Cursor([
                'def test_function[A, B](c, d):',
                '    return [A, B, c, d]',
            ])
        ).last_symbol

        namespace = namespace_module.Namespace()
        test_function.execute(namespace)

        test_func = namespace.lookup('test_function')
        self.assertTrue(callable(test_func[1, 2]))
        self.assertEqual(
            [1, 2, 3, 4],
            test_func[1, 2](3, 4)
        )

    def test_execute_decorator(self):
        test_function: function.Function = function.Function.parse(  # noqa
            parser_module.Cursor([
                '@outer_decorator',
                '@inner_decorator',
                'def test_function(a):',
                '    return [a]',
            ])
        ).last_symbol

        def inner_decorator(func):
            return lambda a: ['inner_decorator', func(a)]

        def outer_decorator(func):
            return lambda a: ['outer_decorator', func(a)]

        namespace = namespace_module.Namespace()
        namespace.declare('inner_decorator', inner_decorator)
        namespace.declare('outer_decorator', outer_decorator)
        test_function.execute(namespace)

        test_func = namespace.lookup('test_function')
        self.assertTrue(callable(test_func))
        self.assertEqual(
            ['outer_decorator', ['inner_decorator', ['arg']]],
            test_func('arg')
        )

    def test_execute_decorator_exception(self):
        test_function: function.Function = function.Function.parse(  # noqa
            parser_module.Cursor([
                '@outer_decorator',
                '@inner_decorator',
                'def test_function(a):',
                '    return [a]',
            ])
        ).last_symbol

        def inner_decorator(_):
            raise RuntimeError('runtime error')

        def outer_decorator(func):
            return lambda a: ['outer_decorator', func(a)]

        namespace = namespace_module.Namespace()
        namespace.declare('inner_decorator', inner_decorator)
        namespace.declare('outer_decorator', outer_decorator)

        with statement.Raise.Outcome.catch(test_function) as get_outcome:
            test_function.execute(namespace)

        outcome = get_outcome()

        self.assertEqual(
            '\n'.join([
                '2, 21: def test_function(a):',
                '                            ^',
                '1, 16: @inner_decorator',
                '                       ^',
                "RuntimeError('runtime error')",
            ]),
            str(outcome)
        )

    def test_parse(self):
        self.assertEqual(
            function.Function.parse(
                parser_module.Cursor([
                    '@decorator_1',
                    '@decorator_2',
                    'def my_function[a](b) -> c:',
                    '    body',
                ])
            ).last_symbol,
            function.Function(
                name='my_function',
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
                arguments=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('b'),
                        is_positional=True,
                        is_keyword=True,
                    )
                ]),
                decorators=[
                    function.Function.Decorator(
                        expression.Variable('decorator_1')
                    ),
                    function.Function.Decorator(
                        expression.Variable('decorator_2')
                    ),
                ],
                return_type=expression.Variable('c'),
            )
        )

        # Bindings are optional.
        self.assertEqual(
            function.Function.parse(
                parser_module.Cursor([
                    '@decorator_1',
                    '@decorator_2',
                    'def my_function(b) -> c:',
                    '    body',
                ])
            ).last_symbol,
            function.Function(
                name='my_function',
                body=statement.Block([
                    statement.Declaration(
                        expression.Variable('body')
                    )
                ]),
                bindings=argument_list.ArgumentList(),
                arguments=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('b'),
                        is_positional=True,
                        is_keyword=True,
                    )
                ]),
                decorators=[
                    function.Function.Decorator(
                        expression.Variable('decorator_1')
                    ),
                    function.Function.Decorator(
                        expression.Variable('decorator_2')
                    ),
                ],
                return_type=expression.Variable('c'),
            )
        )

        # Return type is optional.
        self.assertEqual(
            function.Function.parse(
                parser_module.Cursor([
                    '@decorator_1',
                    '@decorator_2',
                    'def my_function[a](b):',
                    '    body',
                ])
            ).last_symbol,
            function.Function(
                name='my_function',
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
                arguments=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('b'),
                        is_positional=True,
                        is_keyword=True,
                    )
                ]),
                decorators=[
                    function.Function.Decorator(
                        expression.Variable('decorator_1')
                    ),
                    function.Function.Decorator(
                        expression.Variable('decorator_2')
                    ),
                ],
                return_type=None,
            )
        )

        # Decorators are optional.
        self.assertEqual(
            function.Function.parse(
                parser_module.Cursor([
                    'def my_function[a](b) -> c:',
                    '    body',
                ])
            ).last_symbol,
            function.Function(
                name='my_function',
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
                arguments=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('b'),
                        is_positional=True,
                        is_keyword=True,
                    )
                ]),
                decorators=[],
                return_type=expression.Variable('c'),
            )
        )

    def test_parse_errors(self):
        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            function.Function.parse(
                parser_module.Cursor([
                    '@'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            function.Function.parse(
                parser_module.Cursor([
                    '@decorator a'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Decorator, \'def\', \'class\'\)'):
            function.Function.parse(
                parser_module.Cursor([
                    '@decorator'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Identifier\)'):
            function.Function.parse(
                parser_module.Cursor([
                    '@decorator',
                    'def',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'\[\', \'\(\'\)'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\']\'\)'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo[',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'\(\'\)'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo[]',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'\)\'\)'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo[](',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'\:\'\)'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo()',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo() ->',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(\'\:\'\)'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo() -> return_type',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo() -> return_type: foo',
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(Block\)'):
            function.Function.parse(
                parser_module.Cursor([
                    'def foo() -> return_type:',
                ])
            )

    def test_init_locals_arguments(self):
        my_function = function.Function(
            name='func',
            arguments=argument_list.ArgumentList([
                argument_list.Argument(
                    expression.Variable('foo', expression.Variable('a')),
                    is_keyword=True,
                ),
                argument_list.Argument(
                    expression.Variable('bar', expression.Variable('b')),
                    is_keyword=True,
                ),
            ]),
        )

        self.assertEqual(
            {
                'foo': expression.Variable('foo', expression.Variable('a')),
                'bar': expression.Variable('bar', expression.Variable('b')),
            },
            my_function.locals
        )

    def test_init_locals_arguments_repeat_name(self):
        with self.assertRaisesRegex(ValueError, "'foo': repeated argument name not allowed"):
            function.Function(
                name='func',
                arguments=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('foo'),
                        is_keyword=True,
                    ),
                    argument_list.Argument(
                        expression.Variable('foo'),
                        is_keyword=True,
                    ),
                ]),
            )

    def test_init_locals_variables(self):
        my_function = function.Function(
            name='func',
            arguments=argument_list.ArgumentList([
                argument_list.Argument(
                    expression.Variable('foo'),
                    is_positional=True,
                ),
            ]),
            body=statement.Block([
                statement.Assignment(
                    receivers=[expression.Variable('bar')],
                    expression=expression.Variable('foo'),
                ),
                # Assigning back to foo should not cause an error.
                statement.Assignment(
                    receivers=[expression.Variable('foo')],
                    expression=expression.Variable('bar'),
                ),
                # This variable isn't assigned to, so doesn't get included in the local scope.
                statement.Expression(expression.Variable('baz'))
            ]),
        )

        self.assertEqual(
            {
                'foo': expression.Variable('foo'),
                'bar': expression.Variable('bar'),
            },
            my_function.locals
        )

    def test_init_locals_nonlocals(self):
        my_function = function.Function(
            name='func',
            body=statement.Block([
                statement.Assignment(
                    receivers=[expression.Variable('bar')],
                    expression=expression.Variable('foo'),
                ),
                # Although bar is assigned to, it is nonlocal.
                statement.Nonlocal(
                    variables=[expression.Variable('bar')]
                ),
            ]),
        )

        self.assertEqual(
            {},
            my_function.locals
        )

    def test_init_locals_arguments_not_nonlocal(self):
        # Arguments cannot be declared nonlocal.
        with self.assertRaisesRegex(ValueError, 'arguments cannot be declared nonlocal: bar, foo'):
            function.Function(
                name='func',
                arguments=argument_list.ArgumentList([
                    argument_list.Argument(
                        expression.Variable('foo'),
                        is_positional=True,
                    ),
                    argument_list.Argument(
                        expression.Variable('bar'),
                        is_positional=True,
                    ),
                ]),
                body=statement.Block([
                    statement.Nonlocal(
                        variables=[
                            expression.Variable('foo'),
                            expression.Variable('bar'),
                        ]
                    ),
                ]),
            )


class FunctionDecoratorTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(
            function.Function.Decorator.parse(
                parser_module.Cursor([
                    '@foo',
                    'next line',
                ])
            ).last_symbol,
            function.Function.Decorator(
                value=expression.Variable('foo')
            )
        )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected one of \(EndLine\)'):
            function.Function.Decorator.parse(
                parser_module.Cursor([
                    '@foo bar'
                ])
            )

        with self.assertRaisesRegex(parser_module.ParseError, r'expected an operand'):
            function.Function.Decorator.parse(
                parser_module.Cursor([
                    '@'
                ])
            )
