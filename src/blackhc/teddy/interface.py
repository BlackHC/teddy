import dataclasses

from blackhc.implicit_lambda import arg, _


all_keys = slice(None, None, None)


# This ordering is used to ensure that filter and map implicit_lambdas get the right argument order automatically
arg_ordering = ["key", "value", "_"]


_key = arg(0, "key")
_value = arg(0, "value")


@dataclasses.dataclass(frozen=True)
class Literal:
    __slots__ = ("value",)
    value: object


def lit(item):
    return Literal(item)
