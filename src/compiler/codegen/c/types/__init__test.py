import unittest

from .. import types


class TypesTestCase(unittest.TestCase):
    def test_instance_caching(self):
        void_1 = types.Void()
        void_2 = types.Void()

        self.assertIs(void_1, void_2)

        void_ptr_1 = void_1.pointer
        void_ptr_2 = void_2.pointer

        self.assertIs(void_ptr_1, void_ptr_2)

        self.assertNotEqual(void_1, void_ptr_1)

        void_ptr_ptr = void_ptr_1.pointer
        self.assertNotEqual(void_ptr_1, void_ptr_ptr)

    def test_void(self):
        void_t = types.Void()

        self.assertEqual(
            'void',
            void_t.name
        )

        self.assertEqual(
            [],
            list(void_t.render_program_part())
        )

        self.assertEqual(
            [],
            list(void_t.dependencies)
        )

    def test_void_ptr(self):
        void_t = types.Void()
        void_ptr = void_t.pointer

        self.assertEqual(
            '_void_Ptr',
            void_ptr.name
        )

        self.assertEqual(
            [
                'typedef void *_void_Ptr;'
            ],
            list(void_ptr.render_program_part())
        )

        self.assertEqual(
            [
                void_t
            ],
            list(void_ptr.dependencies)
        )

    def test_pointer(self):
        void_t = types.Void()
        void_ptr = types.Pointer(void_t)

        self.assertEqual(
            '_void_Ptr',
            void_ptr.name
        )

        self.assertEqual(
            [
                'typedef void *_void_Ptr;'
            ],
            list(void_ptr.render_program_part())
        )

        self.assertEqual(
            [
                void_t
            ],
            list(void_ptr.dependencies)
        )

    def test_function_pointer(self):
        function_pointer = types.FunctionPointer(
            argument_types=[
                types.Void().pointer,
                types.Void().pointer.pointer,
            ],
            return_type=types.Void(),
        )

        self.assertEqual(
            '__void_Ptr___void_Ptr_Ptr_Returns_void_FnPtr',
            function_pointer.name
        )

        self.assertEqual(
            [
                'typedef void (*__void_Ptr___void_Ptr_Ptr_Returns_void_FnPtr)(',
                ('  ', '_void_Ptr', ','),
                ('  ', '__void_Ptr_Ptr'),
                ');',
            ],
            list(function_pointer.render_program_part())
        )

        self.assertEqual(
            [
                types.Void().pointer,
                types.Void().pointer.pointer,
                types.Void(),
            ],
            list(function_pointer.dependencies)
        )

    def test_struct(self):
        struct = types.Struct(
            name='Foo',
            fields=[
                types.Struct.Field('hello', types.Void()),
                types.Struct.Field('world', types.Void().pointer),
            ],
        )

        self.assertEqual(
            'Foo',
            struct.name
        )

        self.assertEqual(
            [
                'typedef struct {',
                ('  ', 'void hello;'),
                ('  ', '_void_Ptr world;'),
                ('} ', 'Foo', ';'),
            ],
            list(struct.render_program_part())
        )

        self.assertEqual(
            [
                types.Void(),
                types.Void().pointer,
            ],
            list(struct.dependencies)
        )

    def test_union(self):
        union = types.Struct(
            name='Foo',
            fields=[
                types.Struct.Field('hello', types.Void()),
                types.Struct.Field('world', types.Void().pointer),
            ],
        )

        self.assertEqual(
            'Foo',
            union.name
        )

        self.assertEqual(
            [
                'typedef struct {',
                ('  ', 'void hello;'),
                ('  ', '_void_Ptr world;'),
                ('} ', 'Foo', ';'),
            ],
            list(union.render_program_part())
        )

        self.assertEqual(
            [
                types.Void(),
                types.Void().pointer,
            ],
            list(union.dependencies)
        )
