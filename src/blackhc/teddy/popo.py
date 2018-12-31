"""POPO: Plain-old Python object

Teddy interface for making life easier for POPOs.
"""
import json
import prettyprinter
import functools
import operator
import itertools
import dataclasses
import typing


@dataclasses.dataclass
class _NoValue:
    """A None that is not None.

    To allow to differentiate between non-existing expression paths and the ones containing None.
    """
    __slots__= ()

    def __iter__(self):
        return iter(())


# no_value is the only instance of N
no_value = _NoValue()

all_keys = slice(None, None, None)


@dataclasses.dataclass
class Literal:
    __slots__=('value',)
    value: object


def teddy_filter_key_value(f):
    def map_key_item(item):
        if isinstance(item, (list, tuple)):
            return ((i, value) for i, value in enumerate(item) if f(value, i))
        if isinstance(item, dict):
            return ((key, value) for key, value in item.items() if f(value, key))
        if dataclasses.is_dataclass(item):
            results = ((field.name, getattr(item, field.name)) for field in dataclasses.fields(item))
            results = ((key, value) for key, value in results if f(value, key))
        raise NotImplementedError(type(item))
    return map_key_item


def teddy_filter_key(f):
    def map_key_item(item):
        if isinstance(item, (list, tuple)):
            return ((i, value) for i, value in enumerate(item) if f(i))
        if isinstance(item, dict):
            return ((key, value) for key, value in item.items() if f(key))
        if dataclasses.is_dataclass(item):
            results = ((field.name, getattr(item, field.name)) for field in dataclasses.fields(item))
            results = ((key, value) for key, value in results if f(key))
        raise NotImplementedError(type(item))
    return map_key_item


def teddy_item_mapper(f):
    def map_item(item):
        if isinstance(item, (list, tuple, set)):
            return map(f, item)
        if isinstance(item, dict):
            return map(f, item.values())
        if dataclasses.is_dataclass(item):
            return map(f, (getattr(item, field.name) for field in dataclasses.fields(item)))
        raise NotImplementedError(type(item))
    return map_item


def teddy_item_getter(key):
    def getkey(item):
        if isinstance(item, dict):
            return item[key] if key in item else no_value
        if isinstance(item, (list, tuple)):
            return item[key] if -len(item)<=key<len(item) else no_value
        if dataclasses.is_dataclass(item):
            return getattr(item, key) if hasattr(item, key) else no_value
        raise NotImplementedError(type(item))
    return getkey


def teddy_getitem_single(key, preserve_single_value):
    if key == all_keys:
        def outer_all(mapper):
            def inner(item):
                result = list(map(mapper, item))
                if all(r is no_value for r in result):
                    return no_value
                if all(r is not no_value for r in result):
                    return result
                return {i: r for i, r in enumerate(result) if r is not no_value}
            return inner
        return outer_all

    if callable(key):
        # TODO: how do we check signatures?
        argcount = key.__code__.co_argcount
        if argcount == 1:
            filter_item = teddy_filter_key(key)
        elif argcount == 2:
            filter_item = teddy_filter_key_value(key)
        else:
            raise NotImplementedError(f'{key} not supported for filtering (only 1 or 2 arguments)!')

        def outer_filter(mapper):
            def inner(item):
                filtered = filter_item(item)
                results = ((key, mapper(value)) for key, value in filtered)
                results = {key: value for key, value in results if value is not no_value}
                return results if results else no_value
            return inner

        return outer_filter

    if preserve_single_value:
        sub_outer = teddy_getitem_single(key, preserve_single_value=False)

        def outer_preserve_single_value(mapper):
            def inner(item):
                result = sub_outer(mapper)(item)
                if result is not no_value:
                    return {key: result}
                return result
            return inner

        return outer_preserve_single_value

    def outer(mapper):
        getitem = teddy_item_getter(key)

        def inner(item):
            result = getitem(item)
            if result is not no_value:
                result = mapper(result)
            return result
        return inner

    return outer


def teddy_getitem(keys, preserve_single_value):
    if isinstance(keys, list):
        sub_outers = [teddy_getitem(key, preserve_single_value=False) for key in keys]

        def outer_list(mapper):
            sub_mappers = [sub_outer(mapper) for sub_outer in sub_outers]

            def inner(item):
                results = (sub_mapper(item) for sub_mapper in sub_mappers)
                results = [result for result in results if result is not no_value]
                return results if results else no_value
            return inner

        return outer_list

    if isinstance(keys, tuple):
        sub_outers = [teddy_getitem(key, preserve_single_value=False) for key in keys]

        def outer_tuple(mapper):
            sub_mappers = [sub_outer(mapper) for sub_outer in sub_outers]

            def inner(item):
                results = (sub_mapper(item) for sub_mapper in sub_mappers)
                results = tuple(result for result in results if result is not no_value)
                return results if results else no_value
            return inner

        return outer_tuple

    if isinstance(keys, set):
        sub_outers = [(key, teddy_getitem(key, preserve_single_value=False)) for key in keys]

        def outer_set(mapper):
            sub_mappers = ((key, sub_outer(mapper)) for key, sub_outer in sub_outers)

            def inner(item):
                results = ((key, sub_mapper(item)) for key, sub_mapper in sub_mappers)
                results = {key: result for key, result in results if result is not no_value}
                return results if results else no_value
            return inner

        return outer_set

    if isinstance(keys, dict):
        sub_outers = [(name, teddy_getitem(key, preserve_single_value=False)) for name, key in keys.items()]

        def outer_dict(mapper):
            sub_mappers = ((key, sub_outer(mapper)) for key, sub_outer in sub_outers)

            def inner(item):
                results = ((key, sub_mapper(item)) for key, sub_mapper in sub_mappers)
                results = {key: result for key, result in results if result is not no_value}
                return results if results else no_value
            return inner

        return outer_dict

    if isinstance(keys, Literal):
        keys = keys.value

    return teddy_getitem_single(keys, preserve_single_value=preserve_single_value)


def id_func(x):
    return x


@dataclasses.dataclass(frozen=True)
class Teddy:
    # Iterable takes a callable that maps the value to a 1-tuple or empty tuple.
    # The callable takes a value (not a 1-tuple or empty one).
    iterable: typing.Callable
    preserve_single_value: bool

    def _teddy(self, **updates):
        return dataclasses.replace(self, **updates)

    def __iter__(self):
        return iter(self.iterable(id_func))

    def _chain(self, outer):
        return self._teddy(iterable=lambda mapper: self.iterable(outer(mapper)))

    def apply(self, f):
        def outer(mapper):
            def inner(item):
                return mapper(f(item))
            return inner

        return self._chain(outer)

    def __call__(self, f):
        return self.apply(f)

    def map(self, f):
        return self.apply(teddy_item_mapper(f))

    def __getitem__(self, key):
        return self._chain(teddy_getitem(key, preserve_single_value=self.preserve_single_value))

    @property
    def result(self):
        r = self.iterable(id_func)
        return r


@prettyprinter.register_pretty(Teddy)
def repr_teddy(value, ctx):
    return prettyprinter.pretty_call(ctx, type(value), value.iterable(id_func))


def teddy(data, preserve_single_value=True):
    return Teddy(iterable=lambda mapper: mapper(data), preserve_single_value=preserve_single_value)


prettyprinter.install_extras(exclude=['django', 'ipython'])

pprint = functools.partial(prettyprinter.pprint, depth=4)

data = [[1,2], [3,4,5]]

data = teddy(data, preserve_single_value=False)

pprint(data[:][lambda idx: idx % 2 ==0])
pprint(data[0])
pprint(data[0][1])
