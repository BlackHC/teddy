# Iterable Generators

Generators and generator comprehensions in Python are iterators and not iterables.
This means that `iter(generator_comprehension) == generator_comprehension`, and you can
only iterate over a generator once.
