# KeyedSequence

An (read-only) dict that iterates like a sequence, or a sequence that has keys like a dict.

The most straightforward implementation just wraps a `dict` and redefines `__iter__` to iterate over `.values()`

## Indexing

It is easy to add two custom classes `Literal` and `Index` to also support indexing into `tuple(values())` using integer indices instead of doing a key lookup.

However, then we'd want to have a copy of `tuple(values())`.
