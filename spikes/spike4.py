"""Spike4

With an index structure and dead-end paths don't matter.

Spike3 does not support because there is no way to drop (or add) elements.

## Lessons:
* I've essentially implemented an Optional type in Python using tuples.
* map and generators are not restartable in genearl (duh): calling iter on them doesn't do anything
  because they are iterators and not iterables!!!
* a lot of heavy lifting inside mappers
* to simplify, I'd need to implement a function composition function
* supporting culling and potentially adding elements is hard work

Can I implement this without changing the semantics of mappers?

No, only if None were to take on a special meaning.

Can I implement an Optional type that is space efficient?

Yeah, probably.

Can I generate code for this efficiently?

Yeah, probably.

Schemas could help with avoiding such code paths.
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
        return (item[key],) if key in item else ()
    if isinstance(item, (list, tuple)):
        return (item[key],) if -len(item)<=key<len(item) else ()
    if dataclasses.is_dataclass(item):
        return (getattr(item, key),) if hasattr(item, key) else ()
    raise NotImplementedError(type(item))


def id_func(x):
    return x

def nop_mapper(x):
    return (x,)

@dataclasses.dataclass(frozen=True)
class Teddy:
    # Iterable takes a callable that maps the value to a 1-tuple or empty tuple.
    # The callable takes a value (not a 1-tuple or empty one).
    iterable: typing.Callable
    preserve_single_value: bool

    def _teddy(self, **updates):
        return dataclasses.replace(self, **updates)

    def __iter__(self):
        return iter(self.iterable(nop_mapper))

    def apply(self, f):
        return self._teddy(iterable=lambda mapper: self.iterable(lambda item: (mapper(f(item)),)))

    def __call__(self, f):
        return self.apply(f)

    def map(self, f):
        return self.apply(functools.partial(teddy_item_map, f))

    def __getitem__(self, key):
        if key == slice(None, None, None):
            def outer_all(mapper):
                def inner(item):
                    result = tuple(map(mapper, item))
                    if all(not r for r in result):
                        return ()
                    if all(r for r in result):
                        return ([r[0] for r in result],)
                    return ({i: r[0] for i, r in enumerate(result) if r},)
                return self.iterable(inner)
            return self._teddy(iterable=outer_all)

        if self.preserve_single_value:
            def outer_preserving(mapper):
                def inner(item):
                    result = teddy_itemgetter_tuple_or_empty(item, key=key)
                    if result:
                        result = mapper(result[0])
                    if result:
                        return ({key: result[0]},)
                    return ()
                return self.iterable(inner)
            return self._teddy(iterable=outer_preserving)

        def outer(mapper):
            def inner(item):
                result = teddy_itemgetter_tuple_or_empty(item, key=key)
                if result:
                    result = mapper(result[0])
                return result
            return self.iterable(inner)

        return self._teddy(iterable=outer)

    @property
    def result(self):
        r = self.iterable(nop_mapper)
        return r[0] if r else ()


@prettyprinter.register_pretty(Teddy)
def repr_teddy(value, ctx):
    return prettyprinter.pretty_call(ctx, type(value), value.iterable(nop_mapper))


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
