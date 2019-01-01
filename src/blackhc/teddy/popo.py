"""POPO: Plain-old Python object

Implementation details for handling POPOs.
"""
import dataclasses
import functools
import typing

from blackhc.teddy import transformers
from blackhc.teddy import no_value
from blackhc.teddy import interface


@dataclasses.dataclass(frozen=True)
class FiniteGenerator:
    __slots__ = ("generator", "is_sequence")
    generator: typing.Callable[[], typing.Generator]
    is_sequence: bool

    @staticmethod
    def wrap(obj: object):
        kvs = lambda: transformers.to_kv(obj)
        is_seq = isinstance(obj, (list, tuple))
        return FiniteGenerator(kvs, is_seq)

    def adapt(self, transformers: callable, seq_preserving=False):
        return FiniteGenerator(lambda: transformers(self.generator()), self.is_sequence and seq_preserving)

    def filter_keys(self, f):
        return self.adapt(transformers.filter_keys(f), False)

    def filter_values(self, f):
        return self.adapt(transformers.filter_values(f), False)

    def filter(self, f):
        return self.adapt(transformers.filter(f), False)

    def map_keys(self, f):
        return self.adapt(transformers.map_keys(f), False)

    def map_values(self, f):
        return self.adapt(transformers.map_values(f), True)

    def map(self, f):
        return self.adapt(transformers.map(f), False)

    def __iter__(self):
        return self.generator()

    @property
    def result(self):
        return {key: value for key, value in iter(self)}

    @property
    def result_or_nv(self):
        if self.is_sequence:
            result = [value for _, value in iter(self)]
            is_empty = True
            is_full = True
            for item in result:
                if item is no_value:
                    is_full = False
                    if not is_empty:
                        break

                if item is not no_value:
                    is_empty = False
                    if not is_full:
                        break

            if is_empty:
                return no_value
            if is_full:
                return result

        return self.filter_values(no_value).result or no_value


def key_getter(key):
    def get_key(item):
        if isinstance(item, dict):
            return item[key] if key in item else no_value
        if isinstance(item, (list, tuple)):
            return item[key] if -len(item) <= key < len(item) else no_value
        if dataclasses.is_dataclass(item):
            return getattr(item, key) if hasattr(item, key) else no_value
        return no_value

    return get_key


def getitem(keys, preserve_single_index):
    if keys == interface.all_keys:
        return mapper_all

    if isinstance(keys, list):
        return getitem_list(keys)

    if isinstance(keys, tuple):
        return getitem_tuple(keys)

    if isinstance(keys, dict):
        return getitem_dict(keys)

    if dataclasses.is_dataclass(keys) and isinstance(keys, type):
        return getitem_dataclass(keys)

    if callable(keys):
        return getitem_filter(keys)

    if isinstance(keys, interface.Literal):
        keys = keys.value

    if preserve_single_index:
        return getitem_atom_preserve_single_value(keys)

    return getitem_atom(keys)


def getitem_atom_preserve_single_value(key):
    sub_outer = getitem_atom(key)

    def outer(mapper):
        def inner(item):
            result = sub_outer(mapper)(item)
            if no_value(result):
                return {key: result}
            return result

        return inner

    return outer


def getitem_atom(key):
    def outer(mapper):
        getitem = key_getter(key)

        def inner(item):
            result = getitem(item)
            if no_value(result):
                result = mapper(result)
            return result

        return inner

    return outer


def mapper_all(mapper):
    def inner(item):
        return FiniteGenerator.wrap(item).map_values(mapper).result_or_nv

    return inner


def getargcount(f):
    # TODO: how do we check signatures in general?
    return f.__code__.co_argcount


def getitem_filter(f):
    argcount = getargcount(f)
    if argcount == 1:
        filter_item = transformers.filter_keys(f)
    elif argcount == 2:
        filter_item = transformers.filter(f)
    else:
        raise NotImplementedError(f"{f} not supported for filtering (only 1 or 2 arguments)!")

    def outer(mapper):
        def inner(item):
            return FiniteGenerator.wrap(item).adapt(filter_item).map_values(mapper).result_or_nv

        return inner

    return outer


def getitem_dataclass(keys):
    sub_outers = [(field.name, getitem_atom(field.name)) for field in dataclasses.fields(keys)]

    def outer(mapper):
        sub_mappers = [(key, sub_outer(mapper)) for key, sub_outer in sub_outers]

        def inner(item):
            results = ((key, sub_mapper(item)) for key, sub_mapper in sub_mappers)
            results = keys(**{key: value for key, value in results if value is not no_value})
            return results

        return inner

    return outer


def getitem_dict(keys):
    sub_outers = [(name, getitem(key, preserve_single_index=False)) for name, key in keys.items()]

    def outer(mapper):
        sub_mappers = [(key, sub_outer(mapper)) for key, sub_outer in sub_outers]

        def inner(item):
            results = ((key, sub_mapper(item)) for key, sub_mapper in sub_mappers)
            results = {key: result for key, result in results if result is not no_value}
            return results if results else no_value

        return inner

    return outer


def getitem_tuple(keys):
    sub_outers = [(key, getitem(key, preserve_single_index=False)) for key in keys]

    def outer(mapper):
        sub_mappers = [(key, sub_outer(mapper)) for key, sub_outer in sub_outers]

        def inner(item):
            results = ((key, sub_mapper(item)) for key, sub_mapper in sub_mappers)
            results = {key: result for key, result in results if result is not no_value}
            return results if results else no_value

        return inner

    return outer


def getitem_list(keys):
    sub_outers = [getitem(key, preserve_single_index=False) for key in keys]

    def outer(mapper):
        sub_mappers = [sub_outer(mapper) for sub_outer in sub_outers]

        def inner(item):
            results = (sub_mapper(item) for sub_mapper in sub_mappers)
            results = [result for result in results if result is not no_value]
            return results if results else no_value

        return inner

    return outer


def apply(f, args=None, kwargs=None):
    args = args or []
    kwargs = kwargs or {}
    f_partial = functools.partial(f, *args, **kwargs)

    def outer(mapper):
        def inner(item):
            return mapper(f_partial(item))

        return inner

    return outer


def call(args=None, kwargs=None):
    args = args or []
    kwargs = kwargs or {}

    def outer(mapper):
        def inner(item):
            return mapper(item(*args, **kwargs))

        return inner

    return outer


def map_values_or_kv(f):
    # TODO: how do we check signatures in general?
    argcount = getargcount(f)
    if argcount == 1:
        map_item, preserve_sequence = transformers.map_values(f), True
    elif argcount == 2:
        map_item, preserve_sequence = transformers.map(f), False
    else:
        raise NotImplementedError(f"{f} not supported for filtering (only 1 or 2 arguments)!")

    def outer(mapper):
        def inner(item):
            return FiniteGenerator.wrap(item).adapt(map_item, preserve_sequence).map_values(mapper).result_or_nv

        return inner

    return outer


def map_keys(f):
    def outer(mapper):
        def inner(item):
            return FiniteGenerator.wrap(item).map_keys(f).map_values(mapper).result_or_nv

        return inner

    return outer
