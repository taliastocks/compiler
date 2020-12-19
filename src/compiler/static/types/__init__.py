import typing

from . import metatype


def union(name: str, *types: metatype.TypeBase):
    return metatype.Union(name, types)


def singleton(name: str):
    return metatype.Singleton(name)


def enum(name: str, *names: str):
    return union(name, *(singleton(name_) for name_ in names))


def integer_constant(value: int):
    return metatype.Integer(str(value), minimum=value, maximum=value)


def static_array(name: str, item_type: metatype.TypeBase, size: int):
    return metatype.Array(name, item_type, integer_constant(size))


def dynamic_array(name: str, item_type: metatype.TypeBase, length_type: metatype.Integer = None):
    return metatype.Array(name, item_type, length_type or integer)


def struct(name: str, fields: typing.Mapping):
    return metatype.Struct(name, fields)


true = metatype.Singleton('True')
false = metatype.Singleton('False')
boolean = metatype.Union('Boolean', [false, true])

integer = metatype.Integer('Integer', None, None)
int8 = metatype.Integer('int8', -1 << 7, (1 << 7) - 1)
int16 = metatype.Integer('int16', -1 << 15, (1 << 15) - 1)
int32 = metatype.Integer('int32', -1 << 31, (1 << 31) - 1)
int64 = metatype.Integer('int64', -1 << 63, (1 << 63) - 1)
uint8 = metatype.Integer('uint8', 0, (1 << 8) - 1)
uint16 = metatype.Integer('uint16', 0, (1 << 16) - 1)
uint32 = metatype.Integer('uint32', 0, (1 << 32) - 1)
uint64 = metatype.Integer('uint64', 0, (1 << 64) - 1)

string = metatype.String('String')
