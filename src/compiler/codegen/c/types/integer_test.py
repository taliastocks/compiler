import unittest

from . import integer
from .. import include


class TypesTestCase(unittest.TestCase):
    def test_instance_caching(self):
        signed_char = integer.Char()
        unsigned_char = integer.Char(signed=False)

        self.assertNotEqual(signed_char, unsigned_char)
        self.assertIs(unsigned_char, integer.Char(signed=False))

    def test_name(self):
        expected_names = {
            integer.SizeT: 'size_t',
            integer.WCharT: 'wchar_t',
            integer.Char16T: 'char16_t',
            integer.Char32T: 'char32_t',
            integer.Char: 'char',
            integer.Short: 'short',
            integer.Int: 'int',
            integer.Long: 'long',
            integer.LongLong: 'long_long',
            integer.IntMaxT: 'intmax_t',
            integer.IntPtrT: 'intptr_t',
            integer.Int8T: 'int8_t',
            integer.Int16T: 'int16_t',
            integer.Int32T: 'int32_t',
            integer.Int64T: 'int64_t',
            integer.IntLeast8T: 'int_least8_t',
            integer.IntLeast16T: 'int_least16_t',
            integer.IntLeast32T: 'int_least32_t',
            integer.IntLeast64T: 'int_least64_t',
            integer.IntFast8T: 'int_fast8_t',
            integer.IntFast16T: 'int_fast16_t',
            integer.IntFast32T: 'int_fast32_t',
            integer.IntFast64T: 'int_fast64_t',
        }

        self.assertSetEqual(
            set(self.all_integer_classes()),
            set(expected_names.keys())
        )

        for cls, expected_name in expected_names.items():
            self.assertEqual(expected_name, cls().name)

    def test_default_signed(self):
        expected_signeds = {
            integer.SizeT: False,
            integer.WCharT: False,
            integer.Char16T: False,
            integer.Char32T: False,
            integer.Char: True,
            integer.Short: True,
            integer.Int: True,
            integer.Long: True,
            integer.LongLong: True,
            integer.IntMaxT: True,
            integer.IntPtrT: True,
            integer.Int8T: True,
            integer.Int16T: True,
            integer.Int32T: True,
            integer.Int64T: True,
            integer.IntLeast8T: True,
            integer.IntLeast16T: True,
            integer.IntLeast32T: True,
            integer.IntLeast64T: True,
            integer.IntFast8T: True,
            integer.IntFast16T: True,
            integer.IntFast32T: True,
            integer.IntFast64T: True,
        }

        self.assertSetEqual(
            set(self.all_integer_classes()),
            set(expected_signeds.keys())
        )

        for cls, expected_signed in expected_signeds.items():
            self.assertIs(expected_signed, cls().signed)

    def test_unsigned_name_fundamental_int(self):
        expected_names = {
            integer.Char: 'unsigned_char',
            integer.Short: 'unsigned_short',
            integer.Int: 'unsigned_int',
            integer.Long: 'unsigned_long',
            integer.LongLong: 'unsigned_long_long',
        }

        self.assertSetEqual(
            set(self.all_integer_classes(integer.FundamentalIntBase)),
            set(expected_names.keys())
        )

        for cls, expected_name in expected_names.items():
            self.assertEqual(expected_name, cls(signed=False).name)

    def test_unsigned_name_stdint(self):
        expected_names = {
            integer.IntMaxT: 'uintmax_t',
            integer.IntPtrT: 'uintptr_t',
            integer.Int8T: 'uint8_t',
            integer.Int16T: 'uint16_t',
            integer.Int32T: 'uint32_t',
            integer.Int64T: 'uint64_t',
            integer.IntLeast8T: 'uint_least8_t',
            integer.IntLeast16T: 'uint_least16_t',
            integer.IntLeast32T: 'uint_least32_t',
            integer.IntLeast64T: 'uint_least64_t',
            integer.IntFast8T: 'uint_fast8_t',
            integer.IntFast16T: 'uint_fast16_t',
            integer.IntFast32T: 'uint_fast32_t',
            integer.IntFast64T: 'uint_fast64_t',
        }

        self.assertSetEqual(
            set(self.all_integer_classes(integer.StdIntBase)),
            set(expected_names.keys())
        )

        for cls, expected_name in expected_names.items():
            self.assertEqual(expected_name, cls(signed=False).name)

    def test_typedef_fundamental_int(self):
        expected_typedefs = {
            integer.Char: (
                [],
                ['typedef unsigned char unsigned_char;']
            ),
            integer.Short: (
                [],
                ['typedef unsigned short unsigned_short;']
            ),
            integer.Int: (
                [],
                ['typedef unsigned int unsigned_int;']
            ),
            integer.Long: (
                [],
                ['typedef unsigned long unsigned_long;']
            ),
            integer.LongLong: (
                ['typedef long long long_long;'],
                ['typedef unsigned long long unsigned_long_long;']
            ),
        }

        self.assertSetEqual(
            set(self.all_integer_classes(integer.FundamentalIntBase)),
            set(expected_typedefs.keys())
        )

        for cls, (expected_typedef_signed, expected_typedef_unsigned) in expected_typedefs.items():
            self.assertEqual(expected_typedef_signed, list(cls().render_program_part()))
            self.assertEqual(expected_typedef_unsigned, list(cls(signed=False).render_program_part()))

    def test_dependencies(self):
        expected_dependencies = {
            integer.SizeT: [include.Include(path='stddef.h', builtin=True)],
            integer.WCharT: [include.Include(path='stddef.h', builtin=True)],
            integer.Char16T: [include.Include(path='uchar.h', builtin=True)],
            integer.Char32T: [include.Include(path='uchar.h', builtin=True)],
            integer.Char: [],
            integer.Short: [],
            integer.Int: [],
            integer.Long: [],
            integer.LongLong: [],
            integer.IntMaxT: [include.Include(path='stdint.h', builtin=True)],
            integer.IntPtrT: [include.Include(path='stdint.h', builtin=True)],
            integer.Int8T: [include.Include(path='stdint.h', builtin=True)],
            integer.Int16T: [include.Include(path='stdint.h', builtin=True)],
            integer.Int32T: [include.Include(path='stdint.h', builtin=True)],
            integer.Int64T: [include.Include(path='stdint.h', builtin=True)],
            integer.IntLeast8T: [include.Include(path='stdint.h', builtin=True)],
            integer.IntLeast16T: [include.Include(path='stdint.h', builtin=True)],
            integer.IntLeast32T: [include.Include(path='stdint.h', builtin=True)],
            integer.IntLeast64T: [include.Include(path='stdint.h', builtin=True)],
            integer.IntFast8T: [include.Include(path='stdint.h', builtin=True)],
            integer.IntFast16T: [include.Include(path='stdint.h', builtin=True)],
            integer.IntFast32T: [include.Include(path='stdint.h', builtin=True)],
            integer.IntFast64T: [include.Include(path='stdint.h', builtin=True)],
        }

        self.assertSetEqual(
            set(self.all_integer_classes()),
            set(expected_dependencies.keys())
        )

        for cls, expected_deps in expected_dependencies.items():
            self.assertEqual(
                expected_deps,
                list(cls().dependencies)
            )

    @staticmethod
    def all_integer_classes(base_class=integer.IntBase):
        return [
            cls for cls in vars(integer).values()
            if isinstance(cls, type) and issubclass(cls, base_class)
            and cls not in [
                integer.IntBase,
                integer.UCharBase,
                integer.FundamentalIntBase,
                integer.StdIntBase,
            ]
        ]
