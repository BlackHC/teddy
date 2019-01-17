from teddy.keyed_sequence import KeyedSequence, idx


def test_keyed_sequence():
    a = KeyedSequence(((1, 2), (3, 4), (5, 6)))

    assert list(a) == [2, 4, 6]
    assert a[3] == 4
    assert a[idx(1)] == 4
    assert tuple(a.items()) == ((1, 2), (3, 4), (5, 6))
    assert tuple(a.keys()) == (1, 3, 5)
    assert tuple(a.values()) == (2, 4, 6)
    assert repr(a) == "KeyedSequence((1, 2), (3, 4), (5, 6))"


def test_keyed_sequence_bool():
    assert not KeyedSequence(())
    assert KeyedSequence(((1, 1),))


def test_keyed_sequence_fancy_eq():
    assert KeyedSequence(((1, 2), (3, 4))) == {1: 2, 3: 4}
    assert KeyedSequence(((1, 2), (3, 4))) != {3: 4, 1: 2}
    assert KeyedSequence(((1, 2), (3, 4))) == [2, 4]
    assert KeyedSequence(((1, 2), (3, 4))) != [3, 4]


def test_keyed_sequence_fancy_eq_swapped():
    assert {1: 2, 3: 4} == KeyedSequence(((1, 2), (3, 4)))
    assert {3: 4, 1: 2} != KeyedSequence(((1, 2), (3, 4)))
    assert [2, 4] == KeyedSequence(((1, 2), (3, 4)))
    assert [3, 4] != KeyedSequence(((1, 2), (3, 4)))


def test_asterisk_conversions():
    ms = KeyedSequence(((1, 2), (3, 4)))
    assert {**ms} == {3: 4, 1: 2}
    assert [*ms] == [2, 4]


def test_hash():
    ms = KeyedSequence(((1, 2), (3, 4)))
    hash(ms)

    assert {ms: ms}[ms] == ms


def test_constructors():
    assert KeyedSequence(a=1, b=2) == dict(a=1, b=2)
    assert KeyedSequence({1: 2, 2: 3}) == {1: 2, 2: 3}
    assert KeyedSequence(((1, 2), (2, 3))) == {1: 2, 2: 3}
    assert KeyedSequence(zip((1, 2), (2, 3))) == {1: 2, 2: 3}
