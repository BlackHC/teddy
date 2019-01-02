"""POPO: Plain-old Python object

Implementation details for handling POPOs.
"""
import dataclasses
import functools
import typing
import inspect

from blackhc.teddy import transformers
from blackhc.teddy import no_value
from blackhc.teddy import interface
from blackhc.teddy import mapped_sequence

from blackhc.implicit_lambda import to_lambda, is_lambda_dsl


@dataclasses.dataclass(frozen=True)
class FiniteGenerator:
    __slots__ = "generator"
    generator: typing.Callable[[], typing.Generator]

    @staticmethod
    def wrap(obj: object):
        kvs = lambda: transformers.to_kv(obj)
        return FiniteGenerator(kvs)

    def adapt(self, transformers: callable):
        return FiniteGenerator(lambda: transformers(self.generator()))

    def filter_keys(self, f):
        return self.adapt(transformers.filter_keys(f))

    def filter_values(self, f):
        return self.adapt(transformers.filter_values(f))

    def filter(self, f):
        return self.adapt(transformers.filter(f))

    def map_keys(self, f):
        return self.adapt(transformers.map_keys(f))

    def map_values(self, f):
        return self.adapt(transformers.map_values(f))

    def map(self, f):
        return self.adapt(transformers.map(f))

    def __iter__(self):
        return self.generator()

    @property
    def result(self):
        return mapped_sequence.MappedSequence.from_pairs(iter(self))

    @property
    def result_or_nv(self):
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
    # TODO: move the to_lambda calls into dsl!
    if is_lambda_dsl(keys):
        return getitem_filter(keys)

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
                return mapped_sequence.MappedSequence.from_pairs(((key, result),))
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
    if hasattr(f, "args"):
        return len(f.args)
    # TODO: how do we check signatures in general?
    sig = inspect.signature(f)
    return sum(1 for p in sig.parameters.values() if p.kind != p.KEYWORD_ONLY)


def getitem_filter(f):
    f = to_lambda(f, 1, ordering=interface.arg_ordering)
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
            return FiniteGenerator(lambda: results).result_or_nv

        return inner

    return outer


def getitem_tuple(keys):
    # TODO: guess names for keys
    sub_outers = [(key, getitem(key, preserve_single_index=False)) for key in keys]

    def outer(mapper):
        sub_mappers = [(key, sub_outer(mapper)) for key, sub_outer in sub_outers]

        def inner(item):
            results = ((key, sub_mapper(item)) for key, sub_mapper in sub_mappers)
            return FiniteGenerator(lambda: results).result_or_nv

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
    f = to_lambda(f, required_args=1)

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
    f = to_lambda(f, 1, ordering=interface.arg_ordering)

    # TODO: how do we check signatures in general?
    argcount = getargcount(f)
    if argcount == 1:
        map_item = transformers.map_values(f)
    elif argcount == 2:
        map_item = transformers.map(f)
    else:
        raise NotImplementedError(f"{f} not supported for filtering (only 1 or 2 arguments)!")

    def outer(mapper):
        def inner(item):
            return FiniteGenerator.wrap(item).adapt(map_item).map_values(mapper).result_or_nv

        return inner

    return outer


def map_keys(f):
    f = to_lambda(f, 1)

    def outer(mapper):
        def inner(item):
            return FiniteGenerator.wrap(item).map_keys(f).map_values(mapper).result_or_nv

        return inner

    return outer
