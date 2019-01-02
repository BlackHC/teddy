import dataclasses
import pytest

from blackhc.teddy import teddy, lit, _key, _value


simple_list = [1, 2, 3, 4]
simple_dict = dict(a=1, b=2)
double_list = [[1, 2], [3, 4, 5]]


def test_empty_teddy():
    assert list(teddy([])) == []


def test_getitem_atom():
    assert teddy(simple_list)[0].result == 1


def test_getitem_all():
    assert teddy(simple_list)[:].result == simple_list


def test_getitem_preserve_single_index():
    assert teddy(simple_list, preserve_single_index=True)[0].result == {0: 1}


def test_getitem_list():
    assert teddy(simple_list)[0, 1].result == {0: 1, 1: 2}


def test_getitem_dict():
    assert teddy(simple_list)[{"first": 0, "second": 1}].result == {"first": 1, "second": 2}


def test_getitem_filter():
    assert teddy(simple_list)[lambda x: x == 2].result == {2: 3}


def test_getitem_literal():
    assert teddy(simple_list)[lit(1)].result == 2


def test_apply():
    assert teddy(simple_list)[lambda x: x == 2].apply(lambda v: v + 1).result == {2: 4}


def test_call():
    assert teddy(lambda: 1)().result == 1


def test_getitem_filter_kv():
    assert teddy(simple_list)[lambda k, v: v == 2].result == {1: 2}


def test_getitem_map_v():
    assert teddy(simple_list).map(lambda x: x + 1).result == [2, 3, 4, 5]


def test_getitem_map_kv():
    assert teddy(simple_list).map(lambda k, v: (str(k), v - 1)).result == {"0": 0, "1": 1, "2": 2, "3": 3}


def test_getitem_map_k():
    assert teddy(simple_list).map_keys(lambda k: str(k)).result == {"0": 1, "1": 2, "2": 3, "3": 4}


def test_getattr():
    assert teddy(simple_dict).a.result == 1
    assert teddy(simple_dict).b.result == 2


def test_dataclass():
    @dataclasses.dataclass
    class DC2:
        a: int
        b: int

    obj = DC2(1, 2)
    assert teddy(obj).a.result == 1
    assert teddy(obj).b.result == 2


def test_getitem_dataclass():
    @dataclasses.dataclass(frozen=True)
    class DC3:
        a: int
        b: int
        c: int

    @dataclasses.dataclass(frozen=True)
    class DC2:
        a: int
        b: int

    obj = DC3(1, 2, 3)
    assert teddy(obj)[DC2].result == DC2(1, 2)


def test_double_list():
    assert teddy(double_list)[:][:].result == double_list
    assert teddy(double_list)[0][:].result == [1, 2]

    # NOTE: teddy is broken as long as we can't know sure whether we get a list or dict type!
    assert teddy(double_list)[:][0].result == [1, 3]
    assert teddy(double_list)[:][2].result == {1: 5}


def test_getitem_filter():
    assert teddy(simple_list)[_key == 2].result == {2: 3}


def test_apply():
    assert teddy(simple_list)[_key == 2].apply(_value + 1).result == {2: 4}


def test_getitem_filter_kv():
    assert teddy(simple_list)[_key * _value == 0].result == {0: 1}


def test_getitem_map_v():
    assert teddy(simple_list).map(_value + 1).result == [2, 3, 4, 5]


def test_getitem_map_kv():
    from blackhc.implicit_lambda.builtins import str

    assert teddy(simple_list).map((str._(_key), _value - 1)).result == {"0": 0, "1": 1, "2": 2, "3": 3}


def test_getitem_map_k():
    from blackhc.implicit_lambda.builtins import str

    assert teddy(simple_list).map_keys(str._(_key)).result == {"0": 1, "1": 2, "2": 3, "3": 4}


def test_iter():
    result = teddy(double_list)[:][:].result
    iterated = [[x for x in i] for i in result]
    assert result == iterated
