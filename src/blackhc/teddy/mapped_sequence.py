"""A sequence that has custom indices, or a dict that behaves like a sequence."""
import collections.abc as abc
import dataclasses

from blackhc.teddy.interface import Literal, lit

__all__ = ["idx", "lit", "MappedSequence"]

dict_keys = type({}.keys())
dict_values = type({}.values())
dict_items = type({}.items())

@dataclasses.dataclass(frozen=True)
class Index:
    __slots__ = "index"
    index: int


def idx(row):
    return Index(row)


class MappedSequence(abc.Collection):
    __slots__ = ("_data", "_keys", "_values")
    _data: dict
    _keys: tuple
    _values: tuple

    def __init__(self, data, keys, values):
        self._data = data
        self._keys = keys
        self._values = values

    @staticmethod
    def from_pairs(pairs: tuple):
        data = dict(pairs)
        keys = tuple(data.keys())
        values = tuple(data.values())
        return MappedSequence(data, keys, values)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        if isinstance(key, Index):
            return self._values[key.index]
        if isinstance(key, Literal):
            key = key.value
        return self._data[key]

    def keys(self):
        return KeysView(self)

    def values(self):
        return ValuesView(self)

    def __contains__(self, value):
        return value in self._values

    def __reversed__(self):
        return MappedSequence(self._data, tuple(reversed(self._keys)), tuple(reversed(self._values)))

    def items(self):
        return ItemsView(self)

    def get(self, key, default=None):
        return self[key] if key in self._keys else default

    def index(self, value):
        return self._keys[self._values.index(value)]

    def count(self, value):
        return self._values.count(value)

    def __eq__(self, other):
        if isinstance(other, MappedSequence):
            return self._keys == other._keys and self._values == other._values
        if isinstance(other, dict):
            return self._keys == tuple(other.keys()) and self._values == tuple(other.values())
        if isinstance(other, (tuple, list)):
            return self._values == tuple(other)
        return super().__eq__(other)

    def __hash__(self):
        return hash(self._pairs)

    def __repr__(self):
        return f"{type(self).__name__}({tuple(self.items())})"


class MappingView(abc.Sized):
    __slots__ = '_mapping',

    def __init__(self, mapping):
        self._mapping = mapping

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '{0.__class__.__qualname__}({0._mapping!r})'.format(self)



class KeysView(MappingView, abc.Set):

    __slots__ = ()

    @classmethod
    def _from_iterable(self, it):
        return set(it)

    def __contains__(self, key):
        return key in self._mapping._keys

    def __iter__(self):
        return iter(self._mapping._keys)


KeysView.register(dict_keys)


class ItemsView(MappingView, abc.Set):

    __slots__ = ()

    @classmethod
    def _from_iterable(self, it):
        return set(it)

    def __contains__(self, item):
        key, value = item
        try:
            v = self._mapping[key]
        except KeyError:
            return False
        else:
            return v is value or v == value

    def __iter__(self):
        return iter(zip(self._mapping._keys, self._mapping._values))


ItemsView.register(dict_items)


class ValuesView(MappingView, abc.Collection):

    __slots__ = ()

    def __contains__(self, value):
        return value in self._mapping._values

    def __iter__(self):
        return iter(self._mapping._values)


ValuesView.register(dict_values)