from blackhc.teddy import no_value


def test_no_value_call():
    assert no_value(1)
    assert no_value(None)
    assert not no_value(no_value)
