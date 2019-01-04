from collections import abc
import typing
from blackhc.teddy.keyed_sequence import KeyedSequence
from blackhc.teddy.transformers import to_kv, can_kv


class Zipper(abc.Mapping):
    __slots__ = ("_inners","_inner_keys", "_inner_zipper_keys")
    _inners: typing.List[KeyedSequence]
    _inner_keys: set
    _inner_zipper_keys: set

    def __init__(self, generator):
        self._inners = tuple((key, KeyedSequence(to_kv(value))) for key, value in generator)
        self._inner_keys = set.intersection(*(set(inner_value.keys()) for inner_keys, inner_value in self._inners))
        self._inner_zipper_keys = {key for key in self._inner_keys if all(can_kv(inner_value[key]) for inner_key, inner_value in self._inners)}

    def __getitem__(self, key):
        if key not in self._inner_keys:
            raise KeyError(f'{key} not in shared keys {self._inner_keys}!')

        if key in self._inner_zipper_keys:
            return Zipper((inner_key, inner_value[key]) for inner_key, inner_value in self._inners)

        return KeyedSequence((inner_key, inner_value[key]) for inner_key, inner_value in self._inners)

    def __len__(self):
        return len(self._inner_keys)

    def keys(self):
        return self._inner_keys

    def __iter__(self):
        if self._inner_keys:
            return iter(key for key in self._inners[0][1].keys() if key in self._inner_keys)
        return iter(())

    def __hash__(self):
        return hash(self._inners)

    def __repr__(self):
        return repr(self._inners)
