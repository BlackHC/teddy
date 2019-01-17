"""A mapping that supports attributes."""
from collections import abc
import prettyprinter


class AttrMapping(abc.Mapping):
    __slots__ = ("_mapping",)
    _mapping: dict

    def __init__(self, mapping):
        self._mapping = {}
        self._mapping = dict(mapping)

    def __getitem__(self, key):
        return self._mapping[key]

    def __len__(self):
        return len(self._mapping)

    def __iter__(self):
        return iter(self._mapping)

    def __getattr__(self, key):
        return self._mapping[key]

    __repr__ = prettyprinter.pretty_repr
    # def __repr__(self):
    #    return f"{type(self)}{tuple(self._mapping.items())}"


@prettyprinter.register_pretty(AttrMapping)
def repr_teddy(value, ctx):
    return prettyprinter.pretty_call(ctx, type(value).__name__, *value._mapping.items())
