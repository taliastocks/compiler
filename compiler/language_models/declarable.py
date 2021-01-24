from __future__ import annotations

import abc

import attr


@attr.s
class Declarable(metaclass=abc.ABCMeta):
    """A Declarable is an object such as a function or a variable
    which can be declared within a namespace.
    """

    name: str = attr.ib()
