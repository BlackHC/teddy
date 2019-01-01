from blackhc.teddy import interface
from blackhc.teddy.interface import all_keys
from blackhc.teddy.dsl import teddy


def lit(item):
    return interface.Literal(item)


__all__ = [lit, teddy, all_keys]
