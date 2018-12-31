"""Spike to investigate optional values.

Fastest way is to define a new constant that is used instead of None.
"""

OptionalNone = object()


def is_none(value):
    return value is OptionalNone


def optional_call(value, func):
    if value is OptionalNone:
        return OptionalNone
    return func(value)
