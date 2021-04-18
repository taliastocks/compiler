import unittest

from . import namespace


class NamespaceTestCase(unittest.TestCase):
    def test_declare_lookup(self):
        parent = namespace.Namespace()
        child = namespace.Namespace(parent=parent)

        parent.declare('foo', 'parent_foo')
        parent.declare('bar', 'parent_bar')

        child.declare('foo', 'child_foo')
        child.declare('baz', 'child_baz')

        self.assertIs(
            'child_foo',
            child.lookup('foo')
        )
        self.assertIs(
            'child_foo',
            child['foo']
        )
        self.assertIs(
            'parent_bar',
            child.lookup('bar')
        )
        self.assertIs(
            'parent_bar',
            child['bar']
        )
        self.assertIs(
            'child_baz',
            child.lookup('baz')
        )
        self.assertIs(
            'child_baz',
            child['baz']
        )

        with self.assertRaises(KeyError):
            child.lookup('something_else')
