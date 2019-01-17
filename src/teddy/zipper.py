from collections import abc
import typing
from teddy.keyed_sequence import KeyedSequence
from teddy.transformers import to_kv


class Zipper(abc.Mapping):
    __slots__ = ("_branches", "_branch_keys")
    _branches: typing.List[KeyedSequence]
    _branch_keys: set

    def __init__(self, generator):
        # TODO: KeyedSequence(to_kv(value)) is a slow operation. We only need uniform key access.
        self._branches = tuple((key, KeyedSequence(to_kv(value))) for key, value in generator)
        self._branch_keys = set.intersection(*(set(branch_value.keys()) for branch_keys, branch_value in self._branches))

    def __getitem__(self, key):
        if key not in self._branch_keys:
            # raise KeyError(f"{key} not in shared keys {self._branch_keys}!")
            return None

        return KeyedSequence((branch_key, branch_value[key]) for branch_key, branch_value in self._branches)

    def __len__(self):
        return len(self._branch_keys)

    def keys(self):
        return self._branch_keys

    def __iter__(self):
        # _branch_keys is a set and thus not ordered anymore.
        # TODO: do we actually want an ordered set?
        return iter(key for key in self._branches[0][1].keys() if key in self._branch_keys)

    def __hash__(self):
        return hash(self._branches)

    def __repr__(self):
        return f"Zipper{repr(self._branches)}"


class RelaxedZipper(abc.Mapping):
    __slots__ = ("_branches", "_branch_keys")
    _branches: typing.List[KeyedSequence]
    _branch_keys: set

    def __init__(self, generator):
        # TODO: KeyedSequence(to_kv(value)) is a slow operation. We only need uniform key access.
        self._branches = tuple((key, KeyedSequence(to_kv(value))) for key, value in generator)
        self._branch_keys = set.union(*(set(branch_value.keys()) for branch_keys, branch_value in self._branches))

    def __getitem__(self, key):
        if key not in self._branch_keys:
            # raise KeyError(f"{key} not in shared keys {self._branch_keys}!")
            return None
        return KeyedSequence((branch_key, branch_value[key]) for branch_key, branch_value in self._branches if key in branch_value)

    def __len__(self):
        return len(self._branch_keys)

    def keys(self):
        return self._branch_keys

    def __iter__(self):
        return iter(self._branch_keys)

    def __hash__(self):
        return hash(self._branches)

    def __repr__(self):
        return f"RelaxedZipper{repr(self._branches)}"
