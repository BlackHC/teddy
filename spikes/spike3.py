"""Spike 3

With an index structure.
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


def teddy_itemgetter(item, key):
    #if item is None:
    #    return None
    if isinstance(item, (list, tuple, dict)):
        return item[key]
    if dataclasses.is_dataclass(item):
        return getattr(item, key)
    raise NotImplementedError(type(item))


def id_func(x):
    return x


@dataclasses.dataclass(frozen=True)
class Teddy:
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
            return self._teddy(iterable=
                lambda mapper: self.iterable(lambda item: list(map(mapper, item))))

        if self.preserve_single_value:
            return self._teddy(iterable=
                lambda mapper: self.iterable(lambda item: {key: mapper(teddy_itemgetter(item, key=key))}))

        return self.apply(functools.partial(teddy_itemgetter, key=key))

    @property
    def result(self):
        return self.iterable(id_func)


@prettyprinter.register_pretty(Teddy)
def repr_teddy(value, ctx):
    return prettyprinter.pretty_call(ctx, type(value), value.iterable(id_func))


def teddy(data, preserve_single_value=True):
    return Teddy(iterable=lambda mapper: mapper(data), preserve_single_value=preserve_single_value)


prettyprinter.install_extras(exclude=['django', 'ipython'])

pprint = functools.partial(prettyprinter.pprint, depth=3)

data = [[1,2], [3,4,5]]

data = teddy(data, preserve_single_value=False)

pprint(data[0])

# TODO: this should not fail? or maybe it should?
pprint(data[:][2].result)
