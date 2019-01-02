import dataclasses
import functools
import prettyprinter
import typing

from blackhc.teddy import popo


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
        return self.iterable(id_func)

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

    def map(self, f):
        return self._chain(popo.map_values_or_kv(f))

    def map_keys(self, f):
        return self._chain(popo.map_keys(f))

    def __getitem__(self, key):
        return self._chain(popo.getitem(key, preserve_single_index=self.preserve_single_index))

    def __getattr__(self, key):
        return self._chain(popo.getitem(key, preserve_single_index=self.preserve_single_index))

    __repr__ = prettyprinter.pretty_repr


@prettyprinter.register_pretty(Teddy)
def repr_teddy(value, ctx):
    return prettyprinter.pretty_call(ctx, type(value), value.iterable(id_func))


def teddy(data, *, preserve_single_index=False):
    return Teddy(iterable=lambda mapper: mapper(data), preserve_single_index=preserve_single_index)