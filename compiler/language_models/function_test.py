import unittest

import attr

from . import function, expression, statement, argument_list
from .. import parser as parser_module


class FunctionTestCase(unittest.TestCase):
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

    def test_init_is_generator(self):
        my_function = function.Function(
            name='func',
            body=statement.Block([
                statement.Expression(
                    expression.Yield()
                )
            ]),
        )

        self.assertIs(
            True,
            my_function.is_generator
        )

        my_function = function.Function('func')

        self.assertIs(
            False,
            my_function.is_generator
        )

    def test_init_locals_arguments(self):
        @attr.s(frozen=True, slots=True)
        class MyAnnotation(expression.Variable.Annotation):
            my_attr: str = attr.ib()

            def parse(self, _):
                pass

        my_function = function.Function(
            name='func',
            arguments=argument_list.ArgumentList([
                argument_list.Argument(
                    expression.Variable('foo', [MyAnnotation('a')]),
                    is_keyword=True,
                ),
                argument_list.Argument(
                    expression.Variable('bar', [MyAnnotation('b')]),
                    is_keyword=True,
                ),
            ]),
        )

        self.assertEqual(
            {
                'foo': expression.Variable('foo', [MyAnnotation('a')]),
                'bar': expression.Variable('bar', [MyAnnotation('b')]),
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
