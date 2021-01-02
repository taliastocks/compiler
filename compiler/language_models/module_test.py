import unittest

from . import module, function, class_, reference, expression


class ModuleTestCase(unittest.TestCase):
    def test_init_globals(self):
        my_module = module.Module(
            imports=[module.Import('foo', reference.ModuleReference('path.to.foo'))],
            functions=[function.Function('bar')],
            classes=[class_.Class('Baz')],
            variables=[expression.Variable('bip')],
        )

        self.assertEqual(
            {
                'foo': module.Import('foo', reference.ModuleReference('path.to.foo')),
                'bar': function.Function('bar'),
                'Baz': class_.Class('Baz'),
                'bip': expression.Variable('bip'),
            },
            my_module.globals
        )

        with self.assertRaisesRegex(ValueError, r"Variable\(name='foo'\) cannot be declared with the same "
                                                r"name as Function\(name='foo'\)"):
            module.Module(
                functions=[function.Function('foo')],
                variables=[expression.Variable('foo')],
            )
