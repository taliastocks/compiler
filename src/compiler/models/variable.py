import attr

from . import namespace


@attr.s(frozen=True, slots=True)
class Variable(namespace.Declarable):
    """A Variable is a register in a namespace which can hold runtime values.

    NB: variable.Variable should not be confused with expression.Variable, which
    represents an expression which evaluates to the value of a variable in a scope.
    """
