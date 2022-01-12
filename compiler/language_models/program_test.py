import os
import unittest

from ..libs import parser
from . import (
    expression,
    module,
    program as program_module,
    statement,
)


class ProgramTestCase(unittest.TestCase):
    test_files_path: str = os.path.join(
        os.path.dirname(__file__),
        'interpreter_test_files',
    )

    def test_register_package(self):
        self.maxDiff = None  # pylint: disable=invalid-name
        program = program_module.Program()
        program.register_package(
            ['package'],
            os.path.join(self.test_files_path, 'test_load_directory')
        )

        self.assertEqual(
            {
                ('package', 'subdir', 'sub_level'): module.Module(
                    statements=[
                        statement.Declaration(
                            expression.Variable(
                                name='bar',
                                initializer=expression.String(
                                    is_binary=False,
                                    values=[
                                        parser.String('sub_level.sib')
                                    ],
                                )
                            )
                        ),
                    ]
                ),
                ('package', 'top_level'): module.Module(
                    statements=[
                        statement.Declaration(
                            statement.Import(
                                name='sub_level',
                                path=('.', 'subdir', 'sub_level')
                            )
                        ),
                        statement.Declaration(
                            expression.Variable(
                                name='foo',
                                initializer=expression.String(
                                    is_binary=False,
                                    values=[
                                        parser.String('top_level.sib')
                                    ],
                                )
                            )
                        ),
                    ]
                ),
                ('package', 'subdir', 'ignored_file.txt'): b'',
                ('package', 'subdir', 'sub_level.sib'): b"bar = 'sub_level.sib'\n",
                ('package', 'top_level.sib'): b"import .subdir.sub_level\nfoo = 'top_level.sib'\n"
            },
            program.modules
        )

    def test_get_module(self):
        program = program_module.Program()
        program.register_package(
            ['package'],
            os.path.join(self.test_files_path, 'test_load_directory')
        )

        top_level = program.get_module(('package', 'top_level'))

        self.assertEqual(
            'top_level.sib',
            top_level.foo
        )
        self.assertEqual(
            'sub_level.sib',
            top_level.sub_level.bar
        )

        # Only initialize modules once.
        self.assertIs(
            top_level,
            program.get_module(('package', 'top_level'))
        )
