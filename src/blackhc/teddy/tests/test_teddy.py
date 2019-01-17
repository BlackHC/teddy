import dataclasses
import pytest

from blackhc.teddy import teddy, lit, _key, _value, KeyedSequence, _teddy, all_keys
from implicit_lambda import logical_or


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


def test_getitem_tuple():
    assert teddy(simple_list)[0, 1].result == {0: 1, 1: 2}


def test_getitem_dict():
    assert teddy(simple_list)[{"first": 0, "second": 1}].result == {"first": 1, "second": 2}


def test_getitem_list():
    assert teddy(double_list)[[0, 1]][:].result == {k: v for k, v in enumerate(range(1, 6))}


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
    assert teddy(simple_list).map_values(_value + 1).result == [2, 3, 4, 5]


def test_getitem_map_kv():
    from implicit_lambda.builtins import str

    assert teddy(simple_list).map((str._(_key), _value - 1)).result == {"0": 0, "1": 1, "2": 2, "3": 3}


def test_getitem_map_k():
    from implicit_lambda.builtins import str

    assert teddy(simple_list).map_keys(str._(_key)).result == {"0": 1, "1": 2, "2": 3, "3": 4}


def test_iter():
    result = teddy(double_list)[:][:].result
    iterated = [[x for x in i] for i in result]
    assert result == iterated


def test_mappedsequence():
    assert teddy({1: 5, 2: 6, 3: 7})[dict(a=1, b=2)].result == dict(a=5, b=6)

    ms = KeyedSequence(dict(a=1, b=2))
    ms2 = KeyedSequence({1: 5, 2: 6, 3: 7})

    assert teddy(ms2)[ms].result == dict(a=5, b=6)


def test_getitem_teddy():
    assert teddy({1: 5, 2: 6, 3: 7})[teddy(dict(a=1, b=2))].result == dict(a=5, b=6)


def test_zip():
    assert teddy.zip(a={0: 1}, b={0: 5, 2: 3}).result == {0: dict(a=1, b=5)}
    assert teddy(x0=dict(a={0: 1}, b={0: 5, 2: 3}), x1=dict(a={0: 6}, b={0: 9, 2: 3}))[:].zip().result == dict(
        x0={0: dict(a=1, b=5)}, x1={0: dict(a=6, b=9)}
    )
    # TODO: think about this
    # assert teddy.zip([{0: 1}, {0: 5, 2: 3}]).result == {0: dict(a=1, b=5)}


def test_pipe():
    assert teddy(list(range(20))).pipe(
        *(_teddy[logical_or(_value % i != 0, _value == i)] for i in range(2, 6))
    ).result == [1, 2, 3, 5, 7, 11, 13, 17, 19]


def test_groupby():
    assert teddy(
        [
            dict(id=123, name="John"),
            dict(id=123, nickname="Joe"),
            dict(id=123, surname="Miller"),
            dict(id=456, name="Jack"),
            dict(id=456, nickname="Dick"),
            dict(id=456, surname="Black"),
        ]
    ).groupby("id")[:][:][_key != 'id'].result == {
        123: [dict(name="John"), dict(nickname="Joe"), dict(surname="Miller")],
        456: [dict(name="Jack"), dict(nickname="Dick"), dict(surname="Black")],
    }


def test_attr_map():
    assert teddy(a=1, b=2, c=3).to_attr_map().result == dict(a=1, b=2, c=3)
