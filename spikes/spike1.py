"""Spike 1 (12/27)

Try to implement a simple-as-possible Teddy.

# Learnings

* How can we even differentiate between lists and dicts and other types?

Can we just assume that the first element is the type of every element in the list?
Could we use type annotations?
We could validate the whole data structure upfront/on-demand.
We could try to support something generic, but that means dispatch at runtime.
We could try to create a schema from data and use that...

Lots of ways to make it fast if we want to.

We could also use implicit lambdas to create an expression AST and interpret that...

* How can we regenerate the structure?

What does that even mean in the case of map and reduce? How do we create an index structure?

* item, itemornone, and items seem like good ideas
"""
import json
import blackhc.notebook
import prettyprinter
import functools
import operator
import itertools

with open('./data/swapi.json') as f:
    swapi = json.load(f)


class Teddy:
    """Interface with extension methods."""
    def __init__(self, data):
        self.data = list(data)

    def apply(self, f):
        return Teddy(map(f, self.data))

    def __call__(self, f):
        return self.apply(f)

    def map(self, f):
        return self.apply(functools.partial(map, f))

    def reduce(self, f, initial=None):
        return self.apply(functools.partial(functools.reduce, f, initial=initial))

    def __repr__(self):
        return f'teddy({self.data!r})'

    def __getitem__(self, key):
        if key == slice(None, None, None):
            return Teddy(itertools.chain.from_iterable(self.data))
        return Teddy(self.apply(operator.itemgetter(key)))

    @property
    def item(self):
        assert len(self.data) == 1
        return self.data[0]

    @property
    def itemornone(self):
        assert len(self.data) <= 1
        return self.data[0] if self.data else None

    def __iter__(self):
        return iter(self.data)

    @property
    def items(self):
        return self.data

    def __getattr__(self, name):
        return self.apply(operator.attrgetter(name))


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
pprint1(swapi['people'][:]['name'])

for name in swapi['people'][:]['name']:
    print(name)
