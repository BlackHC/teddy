import dataclasses

from blackhc.teddy.mapped_sequence import MappedSequence


def dataclass_to_kv(obj):
    return ((field.name, getattr(obj, field.name)) for field in dataclasses.fields(obj))


def get_dict_or_slots(obj):
    if hasattr(obj, "__dict__"):
        return tuple(obj.__dict__.keys())
    if hasattr(type(obj), "__slots__"):
        return tuple(obj.__slots__)
    return ()


def attrs_to_kv(obj):
    return ((attr, getattr(obj, attr)) for attr in get_dict_or_slots(obj))


def to_kv(obj: object):
    if isinstance(obj, (list, tuple)):
        return ((i, value) for i, value in enumerate(obj))
    if isinstance(obj, dict):
        return ((key, value) for key, value in obj.items())
    if isinstance(obj, MappedSequence):
        return obj.items()
    if dataclasses.is_dataclass(obj):
        return ((key, value) for key, value in dataclass_to_kv(obj))
    raise NotImplementedError(type(obj))


def filter_keys(f):
    return lambda generator: ((key, value) for key, value in generator if f(key))


def filter_values(f):
    return lambda generator: ((key, value) for key, value in generator if f(value))


def filter(f):
    return lambda generator: ((key, value) for key, value in generator if f(key, value))


def map_keys(f):
    return lambda generator: ((f(key), value) for key, value in generator)


def map_values(f):
    return lambda generator: ((key, f(value)) for key, value in generator)


def map(f):
    return lambda generator: (f(key, value) for key, value in generator)


def call_values(*args):
    return lambda generator: ((key, value(*args)) for key, value in generator)
