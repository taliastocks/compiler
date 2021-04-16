import os
import unittest

from . import interpreter
from .language_models import module, statement, expression
from .libs import parser


class ProgramTestCase(unittest.TestCase):
    test_files_path: str = os.path.join(
        os.path.dirname(__file__),
        'interpreter_test_files',
    )

    def test_load_directory(self):
        program = interpreter.Program()
        program.load_directory(
            'package',
            os.path.join(self.test_files_path, 'test_load_directory')
        )

        self.assertEqual(
            {
                'package.subdir.sub_level': module.Module(
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
                        )
                    ]
                ),
                'package.top_level': module.Module(
                    statements=[
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
                        )
                    ]
                ),
            },
            program.modules
        )
