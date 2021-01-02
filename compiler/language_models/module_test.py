import unittest

from . import module, function, class_, path


class ModuleTestCase(unittest.TestCase):
    def test_init_globals(self):
        my_module = module.Module(
            path=path.ModulePath('path.to.module'),
            imports=[module.Import('foo', path.ModulePath('path.to.foo'))],
            functions=[function.Function('bar')],
            classes=[class_.Class('Baz')],
        )

        self.assertEqual(
            {
                'foo': module.Import('foo', path.ModulePath('path.to.foo')),
                'bar': function.Function('bar'),
                'Baz': class_.Class('Baz'),
            },
            my_module.globals
        )
