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
from blackhc.teddy import keyed_sequence

from blackhc.implicit_lambda import to_lambda, is_lambda_dsl
from blackhc.implicit_lambda import args_resolver


@dataclasses.dataclass(frozen=True)
class FiniteGenerator:
    __slots__ = ("generator_lambda",)
    generator_lambda: typing.Callable[[], typing.Generator]

    @staticmethod
    def wrap(obj: object):
        return FiniteGenerator(lambda: transformers.to_kv(obj))

    def adapt(self, transformers: callable):
        new_generator = FiniteGenerator(lambda: transformers(self.generator_lambda()))
        if __debug__:
            new_generator.generator_lambda.previous = self.generator_lambda
        return new_generator

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

    def call_values(self, *args):
        return self.adapt(transformers.call_values(*args))

    def __iter__(self):
        return self.generator_lambda()

    @property
    def result(self):
        return keyed_sequence.KeyedSequence(iter(self))

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
        if isinstance(item, keyed_sequence.KeyedSequence):
            # NOTE: KeyedSequence is a Sequence so we need to check the keys.
            return item[key] if key in item.keys() else no_value
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
        # TODO: guess proper names from keys
        return getitem_dict({key: key for key in keys})

    if isinstance(keys, dict):
        return getitem_dict(keys)

    if dataclasses.is_dataclass(keys) and isinstance(keys, type):
        return getitem_dataclass(keys)

    if callable(keys):
        return getitem_filter(keys)

    if isinstance(keys, keyed_sequence.KeyedSequence):
        return getitem_dict({**keys})

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
                return keyed_sequence.KeyedSequence({key: result})
            return result

        if __debug__:
            inner.mapper_type = ('getitem_atom_preserve_single_value', getitem_atom_preserve_single_value)
            inner.mapper_args = key
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

        if __debug__:
            inner.mapper_type = ('getitem_atom', getitem_atom)
            inner.mapper_args = key
        return inner

    return outer


def mapper_all(mapper):
    def inner(item):
        return FiniteGenerator.wrap(item).map_values(mapper).result_or_nv

    if __debug__:
        inner.mapper_type = ('mapper_all', mapper_all)
    return inner


def getargcount(f):
    if hasattr(f, "args"):
        return len(f.args)
    # TODO: how do we check signatures in general?
    sig = inspect.signature(f)
    return sum(1 for p in sig.parameters.values() if p.kind != p.KEYWORD_ONLY)


def getitem_filter(f):
    f = to_lambda(f, args_resolver=args_resolver.from_allowed_signatures(('_',), ('key',), ('_', 'value'), ('key', 'value'), ('key', '_')))
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

        if __debug__:
            inner.mapper_type = ('getitem_filter', getitem_filter)
            inner.mapper_args = f
        return inner
    return outer


def getitem_dataclass(keys):
    sub_outers = [(field.name, getitem_atom(field.name)) for field in dataclasses.fields(keys)]

    def outer(mapper):
        sub_mappers = [(key, sub_outer(mapper)) for key, sub_outer in sub_outers]

        def inner(item):
            # TODO: We should convert no_value to None here?
            return keys(**FiniteGenerator(lambda: sub_mappers).call_values(item).filter_values(no_value).result)

        if __debug__:
            inner.mapper_type = ('getitem_dataclass', getitem_dataclass)
            inner.mapper_args = keys
        return inner

    return outer


def getitem_dict(mapping):
    sub_outers = [(name, getitem(key, preserve_single_index=False)) for name, key in mapping.items()]

    def outer(mapper):
        sub_mappers = [(key, sub_outer(mapper)) for key, sub_outer in sub_outers]

        def inner(item):
            return FiniteGenerator(lambda: sub_mappers).call_values(item).result_or_nv

        if __debug__:
            inner.mapper_type = ('getitem_dict', getitem_dict)
            inner.mapper_args = mapping
        return inner

    return outer


def getitem_list(keys):
    sub_outers = [(key, getitem(key, preserve_single_index=False)) for key in keys]

    def outer(mapper):
        sub_mappers = [(key, sub_outer(mapper)) for key, sub_outer in sub_outers]

        def inner(item):
            results = FiniteGenerator(lambda: sub_mappers).call_values(item).result
            return list(results.values()) if results else no_value

        if __debug__:
            inner.mapper_type = ('getitem_list', getitem_list)
            inner.mapper_args = keys
        return inner

    return outer


def apply(f, args=None, kwargs=None):
    f = to_lambda(f, args_resolver=args_resolver.flexible_args(required_args=1))

    args = args or []
    kwargs = kwargs or {}
    f_partial = functools.partial(f, *args, **kwargs)

    def outer(mapper):
        def inner(item):
            return mapper(f_partial(item))

        if __debug__:
            inner.mapper_type = ('apply', apply)
            inner.mapper_args = (f, args, kwargs)
        return inner

    return outer


def call(args=None, kwargs=None):
    args = args or []
    kwargs = kwargs or {}

    def outer(mapper):
        def inner(item):
            return mapper(item(*args, **kwargs))

        if __debug__:
            inner.mapper_type = ('call', call)
            inner.mapper_args = (args, kwargs)
        return inner

    return outer


def map_values(f):
    f = to_lambda(f, args_resolver=args_resolver.from_allowed_signatures(('_',), ('value',), ('key', 'value'), ('key', '_')))

    argcount = getargcount(f)
    if argcount == 1:
        map_item = transformers.map_values(f)
    elif argcount == 2:
        map_item = transformers.map(lambda key, value: (key, f(key, value)))
    else:
        raise NotImplementedError(f"{f} not supported for filtering (only 1 or 2 arguments)!")

    def outer(mapper):
        def inner(item):
            result = FiniteGenerator.wrap(item).adapt(map_item).result_or_nv
            if no_value(result):
                result = mapper(result)
            return result

        if __debug__:
            inner.mapper_type = ('map_values', map_values)
            inner.mapper_args = f
        return inner

    return outer

def map_kv(f):
    f = to_lambda(f, args_resolver=args_resolver.from_allowed_signatures(('key', 'value'), ('key', '_')))

    argcount = getargcount(f)
    if argcount != 2:
        raise NotImplementedError(f"{f} not supported for filtering (only 1 or 2 arguments)!")

    def outer(mapper):
        def inner(item):
            result = FiniteGenerator.wrap(item).map(f).result_or_nv
            if no_value(result):
                result = mapper(result)
            return result

        if __debug__:
            inner.mapper_type = ('map_kv', map_kv)
            inner.mapper_args = f
        return inner

    return outer



def map_keys(f):
    f = to_lambda(f, args_resolver=args_resolver.from_allowed_signatures(('_',), ('key',), ('key', 'value'), ('_', 'value')))

    argcount = getargcount(f)
    if argcount == 1:
        map_item = transformers.map_keys(f)
    elif argcount == 2:
        map_item = transformers.map(lambda key, value: (f(key, value), value))
    else:
        raise NotImplementedError(f"{f} not supported for filtering (only 1 or 2 arguments)!")

    def outer(mapper):
        def inner(item):
            result = FiniteGenerator.wrap(item).adapt(map_item).result_or_nv
            if no_value(result):
                result = mapper(result)
            return result


        if __debug__:
            inner.mapper_type = ('map_keys', map_keys)
            inner.mapper_args = f
        return inner

    return outer
