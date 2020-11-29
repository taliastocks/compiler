import unittest

from . import include


class IncludeTestCase(unittest.TestCase):
    def test_render_program_part(self):
        self.assertEqual(
            ['#include <stdint.h>'],
            list(include.Include('stdint.h', builtin=True).render_program_part())
        )
        self.assertEqual(
            ['#include "my_header.h"'],
            list(include.Include('my_header.h', builtin=False).render_program_part())
        )
