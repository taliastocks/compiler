import unittest

from . import expression


class UnpackTestCase(unittest.TestCase):
    def test_variables(self):
        unpack = expression.Unpack([
            expression.Variable('a'),
            expression.Unpack([
                expression.Variable('b'),
                expression.Unpack([
                    expression.Variable('c'),
                    expression.Variable('d'),
                ]),
                expression.Variable('e'),
            ]),
            expression.Variable('f'),
        ])

        self.assertEqual(
            [
                expression.Variable('a'),
                expression.Variable('b'),
                expression.Variable('c'),
                expression.Variable('d'),
                expression.Variable('e'),
                expression.Variable('f'),
            ],
            list(unpack.variables)
        )
