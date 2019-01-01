"""Singleton instance of a hidden class that is empty iterable.

It is callable, only returning false if it the item is no_value.

This makes it easy to filter out no_values using `filter(no_value, iterable)`.
"""

import dataclasses
import sys


@dataclasses.dataclass
class _NoValue:
    """A None that is not None.

    To allow to differentiate between non-existing expression paths and the ones containing None.
    """

    __slots__ = ()

    def __iter__(self):
        return iter(())

    @staticmethod
    def __call__(item):
        return item is not no_value


# no_value is the only accepted instance of NoValue
no_value = _NoValue()


sys.modules[__name__] = no_value
