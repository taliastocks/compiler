from __future__ import annotations

import typing

import attr

from . import declarable, function, expression, reference

# pylint: disable=fixme
from .. import grammar


@attr.s(frozen=True, slots=True)
class Class(declarable.Declarable, grammar.NonTerminal):
    """A Class declaration and definition.
    """
    @attr.s(frozen=True, slots=True)
    class Decorator:
        pass

    bases: typing.Sequence[reference.ClassReference] = attr.ib(converter=tuple, default=(), repr=False)
    declarations: typing.Sequence[declarable.Declarable] = attr.ib(converter=tuple, default=(), repr=False)

    @classmethod
    def production_rules(cls):
        # Placeholder until I get around to writing a real implementation.
        yield from []


@attr.s(frozen=True, slots=True)
class StaticMethod(function.Function.Decorator):
    """Decorator to denote a method as static.

    Static methods are not bound to an instance and do not receive
    the instance as their first argument.
    """


@attr.s(frozen=True, slots=True)
class ClassMethod(function.Function.Decorator):
    """Decorator to denote a method as a class method.

    Class methods are not bound to an instance; instead, they are bound
    to the class and receive the class as their first argument. In particular,
    when a class method is called on a subclass or instance of a subclass, it
    receives the subclass as its first argument.
    """


@attr.s(frozen=True, slots=True)
class Getter(function.Function.Decorator):
    """Decorator to denote a method as a "getter" for an attribute of the same name.

    Accessing the attribute on an instance causes the decorated method to be called.
    The return value of the decorated method is returned as the attribute value.

    This decorator has no effect on class attribute access unless also used in
    conjunction with ClassMethod or StaticMethod. When used with ClassMethod, the
    method is called with the class as its only argument. When used with StaticMethod,
    the method is called with no arguments.
    """


@attr.s(frozen=True, slots=True)
class Setter(function.Function.Decorator):
    """Decorator to denote a method as a "setter" for an attribute of the same name.

    Assigning to the attribute on an instance causes the decorated method to be called
    with the assigned value as its second argument.

    This decorator has no effect on class attribute access unless also used in
    conjunction with ClassMethod or StaticMethod. When used with ClassMethod, the
    method is called with the class as its first argument and the assigned value as
    its second argument. When used with StaticMethod, the method is called with the
    assigned value as its only argument.
    """


@attr.s(frozen=True, slots=True)
class Private(function.Function.Decorator, expression.Variable.Annotation):
    """Decorator/Annotation to denote a method or attribute as "private".

    Private methods/attributes may only be accessed from methods of the same class.
    Subclasses cannot override private methods/attributes; defining a method/attribute
    of the same name in a subclass is allowed, but does not override the implementation
    defined by the parent class (when accessed from the parent class).

    When a private method/attribute shares the same name as a public method/attribute,
    the private method/attribute takes precedence when accessed from methods of the
    same class; when accessed externally, the public method/attribute is used (since
    the private method/attribute is not visible externally).

    TODO: Design a test framework API which provides access to private methods/attributes.
    """


@attr.s(frozen=True, slots=True)
class Protected(function.Function.Decorator, expression.Variable.Annotation):
    """Decorator/Annotation to denote a method or attribute as "protected".

    Protected methods/attributes may only be accessed from methods of the same class,
    or methods of any of its subclasses. Subclasses may override protected methods/attributes
    with their own implementation.

    When a protected method/attribute shares the same name as a public method/attribute,
    the protected method/attribute takes precedence when accessed from methods of the same
    class or methods of any of its subclasses; when accessed externally, the public method/
    attribute is used (since the protected method/attribute is not visible externally).

    TODO: Design a test framework API which provides access to protected methods/attributes.
    """


@attr.s(frozen=True, slots=True)
class Constructor(function.Function.Decorator, expression.Variable.Annotation):
    """Decorator/Annotation to denote a method or attribute as part of the instance constructor.

    Constructor attributes are appended as position_keyword arguments of the same name to the instance
    constructor in the order in which they were declared.

    Constructor methods have their arguments appended to the instance constructor. The instance
    constructor calls these methods in the order in which they were declared, passing through matching
    arguments. Constructor methods which share a name with an attribute are interpreted as factories
    (or converters) for that attribute; that is, their return value is assigned to the attribute.
    Otherwise, constructors cannot return anything. TODO: validation

    Constructor methods cannot be asynchronous. TODO: validation
    Constructor methods may omit the method name.

    TODO: Figure out how to build the instance constructor (repeated argument names, etc).
    """


@attr.s(frozen=True, slots=True)
class Destructor(function.Function.Decorator):
    """Decorator to denote a method as part of the instance destructor.

    Destructor methods are executed in the order in which they were declared.
    Destructor methods may omit the method name.
    """


@attr.s(frozen=True, slots=True)
class Frozen(expression.Variable.Annotation, Class.Decorator):
    """Annotation/Class Decorator to denote an attribute (or all attributes of a class) as frozen.

    Frozen attributes can only be modified during instance construction; afterwards, they are read-only.
    A class with only frozen attributes may be passed by value rather than by reference if the compiler
    determines that this would be more efficient.

    Note that frozen attributes may still be mutable (due to their assigned value being mutable).
    """
