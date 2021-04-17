import unittest

import attr

from . import namespace, declarable


class NamespaceTestCase(unittest.TestCase):
    def test_declare_lookup(self):
        @attr.s
        class MyDeclarable(declarable.Declarable):
            pass

        parent = namespace.Namespace()
        child = namespace.Namespace(parent=parent)

        parent_foo = MyDeclarable('foo')
        parent.declare(parent_foo)
        parent_bar = MyDeclarable('bar')
        parent.declare(parent_bar)

        child_foo = MyDeclarable('foo')
        child.declare(child_foo)
        child_baz = MyDeclarable('baz')
        child.declare(child_baz)

        self.assertIs(
            child_foo,
            child.lookup('foo')
        )
        self.assertIs(
            parent_bar,
            child.lookup('bar')
        )
        self.assertIs(
            child_baz,
            child.lookup('baz')
        )
        self.assertIsNone(child.lookup('something_else'))
