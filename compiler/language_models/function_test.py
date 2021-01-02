import unittest

import attr

from . import function, expression, statement, variable


class FunctionTestCase(unittest.TestCase):
    def test_check_arguments_order(self):
        with self.assertRaisesRegex(ValueError, "'bar': positional_only argument may not appear after "
                                                "positional_keyword argument"):
            function.Function(
                name='func',
                arguments=[
                    function.Function.Argument(
                        expression.Variable('foo'),
                        is_positional=True,
                        is_keyword=True,
                    ),
                    function.Function.Argument(
                        expression.Variable('bar'),
                        is_positional=True,
                    ),
                ],
            )

        # Should not raise.
        function.Function(
            name='func',
            arguments=[
                function.Function.Argument(
                    expression.Variable('foo'),
                    is_positional=True,
                ),
                function.Function.Argument(
                    expression.Variable('bar'),
                    is_positional=True,
                    is_keyword=True,
                ),
            ],
        )
        function.Function(
            name='func',
            arguments=[
                function.Function.Argument(
                    expression.Variable('foo'),
                    is_positional=True,
                    is_keyword=True,
                ),
                function.Function.Argument(
                    expression.Variable('bar'),
                    is_positional=True,
                    is_keyword=True,
                ),
            ],
        )

    def test_check_arguments_repeat_extra(self):
        with self.assertRaisesRegex(ValueError, "'bar': cannot have multiple positional_extra arguments"):
            function.Function(
                name='func',
                arguments=[
                    function.Function.Argument(
                        expression.Variable('foo'),
                        is_positional=True,
                        is_extra=True,
                    ),
                    function.Function.Argument(
                        expression.Variable('bar'),
                        is_positional=True,
                        is_extra=True,
                    ),
                ],
            )

        with self.assertRaisesRegex(ValueError, "'bar': cannot have multiple keyword_extra arguments"):
            function.Function(
                name='func',
                arguments=[
                    function.Function.Argument(
                        expression.Variable('foo'),
                        is_keyword=True,
                        is_extra=True,
                    ),
                    function.Function.Argument(
                        expression.Variable('bar'),
                        is_keyword=True,
                        is_extra=True,
                    ),
                ],
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
        class MyAnnotation(variable.Variable.Annotation):
            my_attr: str = attr.ib()

        my_function = function.Function(
            name='func',
            arguments=[
                function.Function.Argument(
                    expression.Variable('foo', [MyAnnotation('a')]),
                    is_keyword=True,
                ),
                function.Function.Argument(
                    expression.Variable('bar', [MyAnnotation('b')]),
                    is_keyword=True,
                ),
            ],
        )

        self.assertEqual(
            {
                'foo': variable.Variable('foo', [MyAnnotation('a')]),
                'bar': variable.Variable('bar', [MyAnnotation('b')]),
            },
            my_function.locals
        )

    def test_init_locals_arguments_repeat_name(self):
        with self.assertRaisesRegex(ValueError, "'foo': repeated argument name not allowed"):
            function.Function(
                name='func',
                arguments=[
                    function.Function.Argument(
                        expression.Variable('foo'),
                        is_keyword=True,
                    ),
                    function.Function.Argument(
                        expression.Variable('foo'),
                        is_keyword=True,
                    ),
                ],
            )

    def test_init_locals_variables(self):
        my_function = function.Function(
            name='func',
            arguments=[
                function.Function.Argument(
                    expression.Variable('foo'),
                    is_positional=True,
                ),
            ],
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
                'foo': variable.Variable('foo'),
                'bar': variable.Variable('bar'),
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
                arguments=[
                    function.Function.Argument(
                        expression.Variable('foo'),
                        is_positional=True,
                    ),
                    function.Function.Argument(
                        expression.Variable('bar'),
                        is_positional=True,
                    ),
                ],
                body=statement.Block([
                    statement.Nonlocal(
                        variables=[
                            expression.Variable('foo'),
                            expression.Variable('bar'),
                        ]
                    ),
                ]),
            )


class FunctionArgumentTestCase(unittest.TestCase):
    def test_check_is_keyword_or_is_positional(self):
        with self.assertRaisesRegex(ValueError, 'all arguments must be positional or keyword or both'):
            function.Function.Argument(
                variable=expression.Variable('foo'),
                is_positional=False,
                is_keyword=False,
                is_extra=False,
            )

        with self.assertRaisesRegex(ValueError, 'all arguments must be positional or keyword or both'):
            function.Function.Argument(
                variable=expression.Variable('foo'),
                is_positional=False,
                is_keyword=False,
                is_extra=True,
            )

        # Should not raise.
        function.Function.Argument(
            variable=expression.Variable('foo'),
            is_positional=True,
            is_keyword=False,
            is_extra=False,
        )
        function.Function.Argument(
            variable=expression.Variable('foo'),
            is_positional=False,
            is_keyword=True,
            is_extra=False,
        )

    def test_check_is_extra(self):
        # Extra args cannot be both positional and keyword.
        with self.assertRaisesRegex(ValueError, '"extra" arguments cannot be both positional and keyword'):
            function.Function.Argument(
                variable=expression.Variable('foo'),
                is_positional=True,
                is_keyword=True,
                is_extra=True,
            )


class FunctionArgumentPrecedenceTestCase(unittest.TestCase):
    # pylint: disable=protected-access
    def test_from_argument(self):
        self.assertEqual(
            function.Function._ArgumentPrecedence.positional_only,
            function.Function._ArgumentPrecedence.from_argument(
                function.Function.Argument(
                    variable=expression.Variable('foo'),
                    is_positional=True,
                    is_keyword=False,
                    is_extra=False,
                )
            )
        )
        self.assertEqual(
            function.Function._ArgumentPrecedence.positional_keyword,
            function.Function._ArgumentPrecedence.from_argument(
                function.Function.Argument(
                    variable=expression.Variable('foo'),
                    is_positional=True,
                    is_keyword=True,
                    is_extra=False,
                )
            )
        )
        self.assertEqual(
            function.Function._ArgumentPrecedence.positional_extra,
            function.Function._ArgumentPrecedence.from_argument(
                function.Function.Argument(
                    variable=expression.Variable('foo'),
                    is_positional=True,
                    is_keyword=False,
                    is_extra=True,
                )
            )
        )
        self.assertEqual(
            function.Function._ArgumentPrecedence.keyword_only,
            function.Function._ArgumentPrecedence.from_argument(
                function.Function.Argument(
                    variable=expression.Variable('foo'),
                    is_positional=False,
                    is_keyword=True,
                    is_extra=False,
                )
            )
        )
        self.assertEqual(
            function.Function._ArgumentPrecedence.keyword_extra,
            function.Function._ArgumentPrecedence.from_argument(
                function.Function.Argument(
                    variable=expression.Variable('foo'),
                    is_positional=False,
                    is_keyword=True,
                    is_extra=True,
                )
            )
        )
