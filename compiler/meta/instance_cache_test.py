import unittest

import attr

from . import instance_cache


class InstanceCacheTestCase(unittest.TestCase):
    def test_garbage_collection(self):
        events = []

        @attr.s(frozen=True, slots=True)
        class Class(metaclass=instance_cache.InstanceCache):
            field: int = attr.ib()

            def __attrs_post_init__(self):
                events.append((self.field, 'new'))

            def __del__(self):
                events.append((self.field, 'del'))

        instance_1 = Class(1)

        self.assertEqual(
            [(1, 'new')],
            events
        )

        instance_2 = Class(2)

        self.assertNotEqual(instance_1, instance_2)

        self.assertEqual(
            [(1, 'new'), (2, 'new')],
            events
        )

        del instance_2

        self.assertEqual(
            [(1, 'new'), (2, 'new'), (2, 'del')],
            events
        )

        self.assertIs(instance_1, Class(1))

        self.assertEqual(
            [(1, 'new'), (2, 'new'), (2, 'del'), (1, 'new'), (1, 'del')],
            events
        )

        del instance_1

        self.assertEqual(
            [(1, 'new'), (2, 'new'), (2, 'del'), (1, 'new'), (1, 'del'), (1, 'del')],
            events
        )

    def test_distinct_subclass(self):
        @attr.s(frozen=True, slots=True)
        class BaseClass(metaclass=instance_cache.InstanceCache):
            field: int = attr.ib()

        class SubClass1(BaseClass):
            pass

        class SubClass2(BaseClass):
            pass

        instance_1 = SubClass1(1)
        instance_2 = SubClass2(1)

        self.assertNotEqual(instance_1, instance_2)
