"""Spike5

Spike4 with spike_optional_value

Obviously, this does not support adding additional values, but that's fine.

This version still returns full object. This does not scale that well.

# Lessons

* More elegant than using tuples.
* Still need to look into filtering and multi-key selection/ranges.
* Support for [:] for dictionaries
* This version cannot support flattening because it is not using explicit composition.
"""
import json
import blackhc.notebook
import prettyprinter
import functools
import operator
import itertools
import dataclasses
import typing

with open('./data/swapi.json') as f:
    swapi = json.load(f)


@dataclasses.dataclass
class NoValue:
    __slots__= ()

    def __iter__(self):
        return iter(())


no_value = NoValue()


def teddy_item_map(f, item):
    if isinstance(item, (list, tuple)):
        return map(f, item)
    if isinstance(item, dict):
        return map(f, item.values())
    if dataclasses.is_dataclass(item):
        return map(f, (getattr(item, field.name) for field in dataclasses.fields(item)))
    raise NotImplementedError(type(item))


def teddy_itemgetter_tuple_or_empty(item, key):
    if isinstance(item, dict):
        return item[key] if key in item else no_value
    if isinstance(item, (list, tuple)):
        return item[key] if -len(item)<=key<len(item) else no_value
    if dataclasses.is_dataclass(item):
        return getattr(item, key) if hasattr(item, key) else no_value
    raise NotImplementedError(type(item))


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

    def apply(self, f):
        return self._teddy(iterable=lambda mapper: self.iterable(lambda item: mapper(f(item))))

    def __call__(self, f):
        return self.apply(f)

    def map(self, f):
        return self.apply(functools.partial(teddy_item_map, f))

    def __getitem__(self, key):
        if key == slice(None, None, None):
            def outer_all(mapper):
                def inner(item):
                    result = list(map(mapper, item))
                    if all(r is no_value for r in result):
                        return no_value
                    if all(r is not no_value for r in result):
                        return result
                    return {i: r for i, r in enumerate(result) if r is not no_value}
                return self.iterable(inner)
            return self._teddy(iterable=outer_all)

        if self.preserve_single_value:
            def outer_preserving(mapper):
                def inner(item):
                    result = teddy_itemgetter_tuple_or_empty(item, key=key)
                    if result is not no_value:
                        result = mapper(result)
                    if result is not no_value:
                        return {key: result}
                    return no_value
                return self.iterable(inner)
            return self._teddy(iterable=outer_preserving)

        def outer(mapper):
            def inner(item):
                result = teddy_itemgetter_tuple_or_empty(item, key=key)
                if result is not no_value:
                    result = mapper(result)
                return result
            return self.iterable(inner)

        return self._teddy(iterable=outer)

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

pprint(data)
pprint(data[0])
pprint(data[0][1])

pprint(data[:])
pprint(data[:][0].result)
pprint(data[:][2])
pprint(data[:][4].result)

pprint(teddy([[]])[0])
