import unittest

from compiler.meta import generic


class GenericTestCase(unittest.TestCase):
    def test_one_parameter(self):  # noqa
        # pylint: disable=invalid-name
        @generic.Generic
        def MyGeneric(my_param):  # noqa
            # pylint: disable=redefined-outer-name
            class MyClass:
                @staticmethod
                def my_method():
                    return my_param

            return MyClass

        self.assertEqual(
            'foo',
            MyGeneric['foo']().my_method()
        )

        self.assertIs(
            MyGeneric['foo'],
            MyGeneric['foo']
        )

    def test_multiple_parameters(self):  # noqa
        # pylint: disable=invalid-name
        @generic.Generic
        def MyGeneric(param_1, param_2):  # noqa
            # pylint: disable=redefined-outer-name
            class MyClass:
                @staticmethod
                def my_method():
                    return param_1, param_2

            return MyClass

        self.assertEqual(
            ('foo', 'bar'),
            MyGeneric['foo', 'bar']().my_method()
        )

        self.assertIs(
            MyGeneric['foo', 'bar'],
            MyGeneric['foo', 'bar']
        )
