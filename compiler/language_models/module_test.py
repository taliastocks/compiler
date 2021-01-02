import unittest

from . import module, function, class_


class ModuleTestCase(unittest.TestCase):
    def test_init_globals(self):
        my_module = module.Module(
            path='path.to.module'.split('.'),
            imports=[module.Import('foo', 'path.to.foo'.split('.'))],
            functions=[function.Function('bar')],
            classes=[class_.Class('Baz')],
        )

        self.assertEqual(
            {
                'foo': module.Import('foo', 'path.to.foo'.split('.')),
                'bar': function.Function('bar'),
                'Baz': class_.Class('Baz'),
            },
            my_module.globals
        )
