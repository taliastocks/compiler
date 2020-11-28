import textwrap
import unittest

from .. import c
from . import function, statement, expression
from .types import integer


class ProgramTestCase(unittest.TestCase):
    def test_render_program_simple(self):
        my_program = c.Program()
        my_program.add(
            function.Function(
                name='main',
                arguments=[
                    function.Function.Argument(
                        'argc',
                        integer.Int(),
                    ),
                    function.Function.Argument(
                        'argv',
                        integer.Char().pointer.pointer,
                    ),
                ],
                return_type=integer.Int(),
                statements=[
                    statement.DeclarationStatement(
                        name='foo',
                        type=integer.Int8T(),
                    ),
                    statement.ExpressionStatement(
                        expression=expression.Assign(
                            left=expression.Variable('foo'),
                            right=expression.IntegerLiteral(0),
                        )
                    ),
                    statement.WhileStatement(
                        condition=expression.LessThan(
                            left=expression.Variable('foo'),
                            right=expression.IntegerLiteral(10),
                        ),
                        body=statement.ExpressionStatement(
                            expression.Assign(
                                left=expression.Variable('foo'),
                                right=expression.Multiply(
                                    left=expression.Variable('foo'),
                                    right=expression.IntegerLiteral(2),
                                ),
                            ),
                        ),
                    ),
                    statement.ReturnStatement(
                        expression=expression.Variable('foo'),
                    ),
                ],
            )
        )

        self.assertEqual(
            textwrap.dedent('''\
                #include <stdint.h>
                typedef char *_char_Ptr;
                typedef _char_Ptr *__char_Ptr_Ptr;
                int main(
                  int,
                  __char_Ptr_Ptr
                );
                int main(
                  int argc,
                  __char_Ptr_Ptr argv
                ) {
                  int8_t foo;
                  (foo
                    = 0);
                  while (
                    (foo
                      < 10)
                  ) (foo
                    = (foo
                      * 2));
                  return foo;
                }
            ''').strip(),
            '\n'.join(my_program)
        )
