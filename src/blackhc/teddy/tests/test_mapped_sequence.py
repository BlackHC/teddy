from blackhc.teddy.mapped_sequence import MappedSequence, idx


def test_mapped_sequence():
    a = MappedSequence.from_pairs(((1, 2), (3, 4), (5, 6)))

    assert list(a) == [2, 4, 6]
    assert a[3] == 4
    assert a[idx(1)] == 4
    assert tuple(a.items()) == ((1, 2), (3, 4), (5, 6))
    assert tuple(a.keys()) == (1, 3, 5)
    assert tuple(a.values()) == (2, 4, 6)
    assert repr(a) == "MappedSequence(((1, 2), (3, 4), (5, 6)))"


def test_mapped_sequence_bool():
    assert not MappedSequence.from_pairs(())
    assert MappedSequence.from_pairs(((1, 1),))


def test_mapped_sequence_fancy_eq():
    assert MappedSequence.from_pairs(((1, 2), (3, 4))) == {1: 2, 3: 4}
    assert MappedSequence.from_pairs(((1, 2), (3, 4))) != {3: 4, 1: 2}
    assert MappedSequence.from_pairs(((1, 2), (3, 4))) == [2, 4]
    assert MappedSequence.from_pairs(((1, 2), (3, 4))) != [3, 4]


def test_mapped_sequence_fancy_eq_swapped():
    assert {1: 2, 3: 4} == MappedSequence.from_pairs(((1, 2), (3, 4)))
    assert {3: 4, 1: 2} != MappedSequence.from_pairs(((1, 2), (3, 4)))
    assert [2, 4] == MappedSequence.from_pairs(((1, 2), (3, 4)))
    assert [3, 4] != MappedSequence.from_pairs(((1, 2), (3, 4)))
