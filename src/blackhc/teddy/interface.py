import dataclasses


all_keys = slice(None, None, None)


@dataclasses.dataclass(frozen=True)
class Literal:
    __slots__ = ("value",)
    value: object
