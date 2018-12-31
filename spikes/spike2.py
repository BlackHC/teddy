"""Spike 2

Add support for handling lists, tuples, dicts, dataclasses and unknown objects differently.

Don't add support for an index structure.
"""
import json
import blackhc.notebook
import prettyprinter
import functools
import operator
import itertools
import dataclasses

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
    if isinstance(item, (list, tuple, dict)):
        return item[key]
    if dataclasses.is_dataclass(item):
        return getattr(item, key)
    raise NotImplementedError(type(item))


def teddy_attrgetter(item, key):
    if isinstance(item, (list, tuple)):
        # Unwrap one level automatically.
        # Use itemgetter which doesn't perform more magic.
        return list(map(functools.partial(teddy_itemgetter, key=key), item))
    if isinstance(item, dict):
        return (item[key],)
    if dataclasses.is_dataclass(item):
        return (getattr(item, key),)
    raise NotImplementedError(type(item))


class Teddy:
    """Interface with extension methods."""
    def __init__(self, data):
        self.data = list(data)

    def apply(self, f):
        return Teddy(map(f, self.data))

    def __call__(self, f):
        return self.apply(f)

    def map(self, f):
        return self.apply(functools.partial(teddy_item_map, f))

    def reduce(self, f, initial=None):
        # TODO
        return self.apply(functools.partial(functools.reduce, f, initial=initial))

    def __repr__(self):
        return f'teddy({self.data!r})'

    def __getitem__(self, key):
        if key == slice(None, None, None):
            assert not self.data or isinstance(self.data[0], (list, tuple))
            # TODO: how to handle dicts etc?
            return Teddy(itertools.chain.from_iterable(self.data))
        return self.apply(functools.partial(teddy_itemgetter, key=key))

    def __iter__(self):
        return iter(self.data)

    @property
    def item(self):
        assert len(self.data) == 1
        return self.data[0]

    @property
    def itemornone(self):
        assert len(self.data) <= 1
        return self.data[0] if self.data else None

    @property
    def items(self):
        return self.data

    def __getattr__(self, key):
        # NOTE: this is such a mess but seems to work?
        # NOPE DOES NOT WORK!
        # data.a[:].b != data.a.b but
        # data.a[:].b == data.a.b[:]
        return Teddy(list(itertools.chain.from_iterable(map(functools.partial(teddy_attrgetter, key=key), self.data))))


@prettyprinter.register_pretty(Teddy)
def repr_teddy(value, ctx):
    return prettyprinter.pretty_call(ctx, type(value), value.data)

prettyprinter.install_extras()

def teddy(obj):
    return Teddy([obj])

pprint1 = functools.partial(prettyprinter.pprint, depth=2)

data = [[1,2], [3,4,5]]

data = teddy(data)

pprint1(data[0][1])

swapi = teddy(swapi)

#pprint1(swapi['people'][:]['name'], depth=3)
#pprint1(swapi.people[:].name, max_seq_len=5)
pprint1(swapi.people[:].name.items, max_seq_len=10)
pprint1(swapi.people.name.items, max_seq_len=10)


#data = [dict(a = [dict(b=[dict(c=1) for _ in range(3)]) for _ in range(3)]) for _ in range(3)]
#data = teddy(data)

#pprint1(data.a.b.c)


"""
l = [{a: [{b: 1}, {b: 2}]}, {a: [{b: 3}, {b: 4}]}]

l.a -> [[{b: 1}, {b: 2}], [{b: 3}, {b: 4}]]

l.a.b -> [1, 2, 3, 4]

What about: l.a[0] -> [{b: 1}, {b: 3}]

Okay, so let's assume that every projection adds a dimension to our data. This only makes sense when we have indexing!
Then l[:].a.b could be different from l.a[:].b and l.a.b[:] as follows:

l[0] = {a: [{b: 1}, {b: 2}]}
l.a.b = [1, 2, 3, 4]

l.a[:]
"""
