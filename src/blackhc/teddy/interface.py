import dataclasses

from blackhc.implicit_lambda import arg, _


all_keys = slice(None, None, None)


# In general only, _, _key and _value will be allowed as implicit lambda signatures.
_key = arg(0, "key")
_value = arg(0, "value")


@dataclasses.dataclass(frozen=True)
class Literal:
    __slots__ = ("value",)
    value: object


def lit(item):
    return Literal(item)
