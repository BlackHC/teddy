"""Spike 7 Re dict types"""
import dataclasses
import collections
from collections import abc


@dataclasses.dataclass
class Index:
    __slots__ = "index"
    index: int


def idx(row):
    return Index(row)


# For lack of better name.
@dataclasses.dataclass
class IndexedSequence:
    __slots__ = ("data", "_values")
    data: dict
    _values: list

    @staticmethod
    def from_pairs(pairs: list):
        data = dict(pairs)
        return IndexedSequence(data, list(data.values()))

    def __iter__(self):
        return iter(self.data.values())

    def items(self):
        return self.pairs

    def keys(self):
        return self.data.keys()

    def values(self):
        return self._values

    def __getitem__(self, key):
        if isinstance(key, Index):
            return self._values[key.index]
        return self.data[key]


def test_indexed_sequence():
    a = IndexedSequence.from_pairs(((1, 2), (3, 4), (5, 6)))

    assert list(a) == [2, 4, 6]
    assert a[3] == 4
    assert a[idx(1)] == 4


class IndexedMapping(abc.Mapping):
    __slots__ = ("_data", "_pairs")
    _data: dict
    _pairs: tuple

    def __init__(self, pairs: tuple):
        self._data = dict(pairs)
        self._pairs = tuple(self._data.items())

    def __iter__(self):
        return iter(self._data.values())

    def __len__(self):
        return len(self._pairs)

    def __getitem__(self, key):
        if isinstance(key, Index):
            return self._pairs[key.index][1]
        return self._data[key]

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __contains__(self, item):
        return item in self.values()

    def get(self, key, default=None):
        return self[key] if key in self._data.keys() else default

    def __eq__(self, other):
        if isinstance(other, IndexedMapping):
            return self._pairs == other._pairs
        return super().__eq__(other)

    def __hash__(self):
        return hash(self._pairs)

    def __repr__(self):
        return f"{type(self).__name__}({self._pairs})"


def test_indexed_mapping():
    a = IndexedMapping(((1, 2), (3, 4), (5, 6)))

    assert list(a) == [2, 4, 6]
    assert a[3] == 4
    assert a[idx(1)] == 4
    assert tuple(a.items()) == ((1, 2), (3, 4), (5, 6))
    assert tuple(a.keys()) == (1, 3, 5)
    assert tuple(a.values()) == (2, 4, 6)
    assert repr(a) == "IndexedMapping(((1, 2), (3, 4), (5, 6)))"
