import dataclasses
import functools
import prettyprinter
import typing

from blackhc.teddy import popo
from blackhc.teddy import zipper
from blackhc.teddy import attr_mapping

from implicit_lambda import to_lambda

def id_func(x):
    return x


@dataclasses.dataclass(frozen=True)
class Teddy:
    # Iterable is callable that can take a mapper that knows how to apply further transformations
    # and returns a callable that applies all transformations to a value.
    # It returns either a value or no_value. (It does not take no_value.)
    iterable: typing.Callable
    preserve_single_index: bool

    @property
    def result(self):
        try:
            return self.iterable(id_func)
        except Exception:
            raise RuntimeError("Result computation error")

    def _teddy(self, **updates):
        return dataclasses.replace(self, **updates)

    def __iter__(self):
        return iter(self.result)

    def _chain(self, outer):
        return self._teddy(iterable=lambda mapper: self.iterable(outer(mapper)))

    def apply(self, f=None, *, args=None, kwargs=None):
        if f is not None:
            return self._chain(popo.apply(f, args, kwargs))
        return self._chain(popo.call(args, kwargs))

    def __call__(self, f=None):
        return self.apply(f)

    def map_values(self, f):
        return self._chain(popo.map_values(f))

    def map(self, f):
        return self._chain(popo.map_kv(f))

    def map_keys(self, f):
        return self._chain(popo.map_keys(f))

    def zip(self):
        return self._chain(popo.zip)

    def groupby(self, keys, drop_none_keys=False, preserve_single_index=None):
        preserve_single_index = preserve_single_index or self.preserve_single_index
        return self._chain(popo.groupby(keys, drop_none_keys=drop_none_keys, preserve_single_index=preserve_single_index))

    def pipe(self, *teddy_exprs, preserve_single_index=None):
        preserve_single_index = preserve_single_index or self.preserve_single_index
        # Teddy is callable so would pass through.
        teddy_exprs = [to_lambda(teddy_expr) for teddy_expr in teddy_exprs]

        mappers = []

        for teddy_expr in teddy_exprs:
            if not isinstance(teddy_expr, Teddy):
                expr_teddy = teddy_expr(_teddy)
            else:
                # Assume, it's a zombie Teddy if teddy_expr is a Teddy.
                expr_teddy = teddy_expr
            mappers.append(expr_teddy.iterable(id_func))

        return self._chain(popo.pipe(mappers))


    def to_attr_map(self):
        return self(attr_mapping.AttrMapping)


    def __getitem__(self, key):
        if isinstance(key, Teddy):
            key = key.result

        return self._chain(popo.getitem(key, preserve_single_index=self.preserve_single_index))

    def __getattr__(self, key):
        return self._chain(popo.getitem(key, preserve_single_index=self.preserve_single_index))

    __repr__ = prettyprinter.pretty_repr
    # def __repr__(self):
    #    return f"{type(self)}({self.result})"


@prettyprinter.register_pretty(Teddy)
def repr_teddy(value, ctx):
    try:
        return prettyprinter.pretty_call(ctx, type(value), value.result)
    except Exception as e:
        return prettyprinter.pretty_call(ctx, type(value), e)


def teddy(data=None, *, preserve_single_index=False, **kwargs):
    if data and kwargs:
        raise SyntaxError('teddy can either be initialized using a tuple or using keywords!')
    data = data or kwargs
    return Teddy(iterable=lambda mapper: mapper(data), preserve_single_index=preserve_single_index)


_teddy = Teddy(iterable=id_func, preserve_single_index=False)

teddy.zip = lambda data=None, *, preserve_single_index=False, **kwargs: teddy(data, **kwargs, preserve_single_index=preserve_single_index).zip()
