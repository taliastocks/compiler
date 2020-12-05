import unittest

from . import declaration


class NamespaceTestCase(unittest.TestCase):
    def test_name(self):
        root = declaration.Namespace()
        self.assertIsNone(root.name)

        child = root['child']
        self.assertEqual('child', child.name)
        self.assertEqual(['child'], list(child.path))

    def test_path(self):
        root = declaration.Namespace()
        child = root['child']
        grandchild = child['grandchild']

        self.assertEqual(
            ['child'],
            list(child.path)
        )
        self.assertEqual(
            ['child', 'grandchild'],
            list(grandchild.path)
        )

    def test_parent(self):
        root = declaration.Namespace()
        child = root['child']
        grandchild = child['grandchild']

        self.assertIs(
            grandchild.parent,
            child
        )
        self.assertIs(
            child.parent,
            root
        )
        self.assertIsNone(root.parent)

    def test_members(self):
        # pylint: disable=pointless-statement
        root = declaration.Namespace()
        root['child1']  # noqa
        root['child2']  # noqa

        self.assertEqual(
            [
                root['child1'],
                root['child2'],
            ],
            list(root.members)
        )

    def test_declaration(self):
        class MyDeclaration(declaration.DeclarationBase):
            pass

        root = declaration.Namespace()
        child = root['child']

        my_declaration = MyDeclaration('Name', child)
        self.assertIs(
            child,
            my_declaration.namespace
        )
        self.assertIs(
            'Name',
            my_declaration.name
        )
        self.assertIs(
            my_declaration,
            child['Name'].declaration
        )

        with self.assertRaises(ValueError) as exc:
            MyDeclaration('Name', child)

        self.assertEqual(
            "['child', 'Name'] already declared",
            str(exc.exception)
        )

        with self.assertRaises(ValueError) as exc:
            root['Name'].declaration = my_declaration

        self.assertEqual(
            'declaration.namespace must be the parent namespace',
            str(exc.exception)
        )

        with self.assertRaises(ValueError) as exc:
            child['OtherName'].declaration = my_declaration

        self.assertEqual(
            'declaration.name must match this namespace',
            str(exc.exception)
        )

    def test_resolve(self):
        # pylint: disable=pointless-statement
        root = declaration.Namespace()
        root['child1']['grandchild1']  # noqa
        root['child1']['conflict']  # noqa
        root['child2']['grandchild1']  # noqa
        root['conflict']  # noqa

        self.assertIs(
            root['child1'],
            root.resolve('child1')
        )
        self.assertIs(
            root['child1'],
            root['child1'].resolve('child1')
        )
        self.assertIs(
            root['child1']['grandchild1'],
            root['child1'].resolve('grandchild1')
        )
        self.assertIs(
            root['child1']['conflict'],
            root['child1'].resolve('conflict')
        )
        self.assertIs(
            root['conflict'],
            root['child2'].resolve('conflict')
        )

        with self.assertRaises(KeyError) as exc:
            root.resolve('grandchild1')

        self.assertEqual(
            "'grandchild1'",
            str(exc.exception)
        )
