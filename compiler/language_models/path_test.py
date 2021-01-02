import unittest

from . import path as path_module


class PathTestCase(unittest.TestCase):
    def test_init_path(self):
        path = path_module.Path('path.to.Something')

        self.assertEqual(
            ('path', 'to', 'Something'),
            path.path
        )
