import pytest
import dataclasses
from blackhc.teddy import transformers
from blackhc.teddy import keyed_sequence


def test_dataclass_to_kv():
    @dataclasses.dataclass
    class DC0:
        pass

    assert tuple(transformers.dataclass_to_kv(DC0())) == ()

    @dataclasses.dataclass
    class DC2:
        a: str
        b: int

    assert tuple(transformers.dataclass_to_kv(DC2("Hello", 1))) == (("a", "Hello"), ("b", 1))


def test_get_dict_or_slots():
    class Empty:
        pass

    assert tuple(transformers.get_dict_or_slots(Empty())) == ()

    class Dict:
        def __init__(self):
            self.a = 1
            self.b = 2

    assert tuple(transformers.get_dict_or_slots(Dict())) == ("a", "b")

    class Slots:
        __slots__ = ("a", "b")

        def __init__(self):
            self.a = 1
            self.b = 1

    assert tuple(transformers.get_dict_or_slots(Slots())) == ("a", "b")


def test_attrs_to_kv():
    class Empty:
        pass

    assert tuple(transformers.attrs_to_kv(Empty())) == ()

    class Dict:
        def __init__(self):
            self.a = 1
            self.b = 2

    assert tuple(transformers.attrs_to_kv(Dict())) == (("a", 1), ("b", 2))

    class Slots:
        __slots__ = ("a", "b")

        def __init__(self):
            self.a = 1
            self.b = 2

    assert tuple(transformers.attrs_to_kv(Slots())) == (("a", 1), ("b", 2))


def test_to_kv():
    assert tuple(transformers.to_kv((1, 2, 3))) == ((0, 1), (1, 2), (2, 3))
    assert tuple(transformers.to_kv([1, 2, 3])) == ((0, 1), (1, 2), (2, 3))
    assert tuple(transformers.to_kv(dict(a=1, b=2))) == (("a", 1), ("b", 2))

    @dataclasses.dataclass
    class DC2:
        a: int
        b: int

    assert tuple(transformers.to_kv(DC2(1, 2))) == (("a", 1), ("b", 2))

    ms = keyed_sequence.KeyedSequence({1: 2, 2: 3})
    assert tuple(transformers.to_kv(ms)) == ((1, 2), (2, 3))


def test_filter_keys():
    assert tuple(transformers.filter_keys(lambda key: True)(transformers.to_kv(tuple(range(3))))) == tuple(
        (i, i) for i in range(3)
    )
    assert tuple(transformers.filter_keys(lambda key: key == 0)(transformers.to_kv(tuple(range(3, 6))))) == ((0, 3),)
    assert tuple(transformers.filter_keys(lambda key: False)(transformers.to_kv(tuple(range(3))))) == tuple()


def test_filter_values():
    assert tuple(transformers.filter_values(lambda value: True)(transformers.to_kv(tuple(range(3))))) == tuple(
        (i, i) for i in range(3)
    )
    assert tuple(transformers.filter_values(lambda value: value == 3)(transformers.to_kv(tuple(range(3, 6))))) == (
        (0, 3),
    )
    assert tuple(transformers.filter_values(lambda value: False)(transformers.to_kv(tuple(range(3))))) == tuple()


def test_filter():
    assert tuple(transformers.filter(lambda key, value: True)(transformers.to_kv(tuple(range(3))))) == tuple(
        (i, i) for i in range(3)
    )
    assert tuple(transformers.filter(lambda key, value: value * key == 0)(transformers.to_kv(tuple(range(3, 6))))) == (
        (0, 3),
    )
    assert tuple(transformers.filter(lambda key, value: False)(transformers.to_kv(tuple(range(3))))) == tuple()


def test_map_keys():
    assert tuple(transformers.map_keys(lambda key: key + 1)(((0, 10), (1, 11)))) == ((1, 10), (2, 11))


def test_map_values():
    assert tuple(transformers.map_values(lambda value: value + 1)(((-10, 0), (-9, 1)))) == ((-10, 1), (-9, 2))


def test_map():
    assert tuple(transformers.map(lambda key, value: (key + 1, value + 2))(((0, 1), (2, 3)))) == ((1, 3), (3, 5))


def test_call_values():
    assert tuple(transformers.call_values(1)(((0, lambda x: x + 1), (1, lambda x: x + 2)))) == ((0, 2), (1, 3))
