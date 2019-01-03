"""Spike6

Using implicit_lambda to build expressions.
"""
import json
import blackhc.notebook
import prettyprinter
import functools
import operator
import itertools
import dataclasses
import typing
from implicit_lambda import _, to_lambda, inline_expr, get_expr, literal, call
from implicit_lambda.details import expression
from implicit_lambda.details import lambda_dsl


with open("./data/swapi.json") as f:
    swapi = json.load(f)


@dataclasses.dataclass
class NoValue:
    __slots__ = ()

    def __iter__(self):
        return iter(())


no_value = NoValue()


def id_func(x):
    return x


@dataclasses.dataclass(frozen=True)
class Teddy:
    # Iterable takes a callable that maps the value to a 1-tuple or empty tuple.
    # The callable takes a value (not a 1-tuple or empty one).
    expr_builders: typing.Tuple[typing.Callable[[lambda_dsl.LambdaDSL], lambda_dsl.LambdaDSL]]

    def _teddy(self, sub_expr_builder):
        return Teddy(self.expr_builders + (sub_expr_builder,))

    def _chain(self, f):
        def chainer(expr):
            return lambda_dsl.call(f, expr)

        return self._teddy(chainer)

    def _expr(self):
        expr = _
        for expr_builder in reversed(self.expr_builders):
            expr = expr_builder(expr)
        return expr

    def __iter__(self):
        return iter(to_lambda(self._expr())())

    def __getitem__(self, key):
        if key == slice(None, None, None):

            def mapper(expr):
                chain = to_lambda(expr)

                def iterate(item):
                    return list(map(chain, item))

                return lambda_dsl.call(iterate, _)

            return self._teddy(mapper)

        def get_item(item):
            return item[key]

        return self._chain(get_item)

    @property
    def result(self):
        return to_lambda(self._expr())()


@prettyprinter.register_pretty(Teddy)
def repr_teddy(value, ctx):
    return prettyprinter.pretty_call(ctx, type(value), value.result)


def teddy(data, preserve_single_value=True):
    return Teddy(expr_builders=(lambda expr: call(expr, data),), preserve_single_value=preserve_single_value)


prettyprinter.install_extras(exclude=["django", "ipython"])

pprint = functools.partial(prettyprinter.pprint, depth=4)

data = [[1, 2], [3, 4, 5]]

data = teddy(data, preserve_single_value=False)

pprint(data)
pprint(data[0])
pprint(data[0][1])

pprint(data[:])
pprint(data[:][0].result)
# pprint(data[:][2])
# pprint(data[:][4].result)

# pprint(teddy([[]])[0])
