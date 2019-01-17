# Teddy

~~Teddy is not Pandas. Teddy is lightweight and snuggly.~~

~~Teddy is straightforward and understands you. Teddy loves you.~~

More importantly, Teddy is not ready for prime time.

## Feature overview

Teddy loves you so much, it will work with vanilla Python types.

```python
from collections
record = namedtuple
data = list()
```

## Python WTFs

### `__getattr__` also gets called for third-party AttributeErrors

Default attribute access does also forward to your `__getattr__` if a property descriptor raises
an unrelated `AttributeError`.

```
In [6]: class A:
   ...:     @property
   ...:     def result(self):
   ...:         return [1,2].a
   ...:
   ...:     def __getattr__(self, key):
   ...:         print('hah')
   ...:

In [7]: A().result
hah
```

### `inspect.signature` doesn't get along with `@staticmethod` in custom object

```
Python 3.7.1 (default, Dec 10 2018, 22:54:23) [MSC v.1915 64 bit (AMD64)]
Type 'copyright', 'credits' or 'license' for more information
IPython 7.2.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import inspect

In [2]: class A:
   ...:     @staticmethod
   ...:     def __call__(x,y):
   ...:         return y
   ...:

In [3]: inspect.signature(A())
Out[3]: <Signature (y)>

In [4]: inspect.signature(A().__call__)
Out[4]: <Signature (x, y)>
```

## TODOs

* [ ] the code could become simpler if it used key, value pairs everywhere internally?
* [ ] tests for attr_mapping
* [ ] prettyprinter is a bit meh sometimes
* [x] I need a read-only wrapper around dicts for using attrs instead of indexing.
* [x] get rid of no_value?
* [x] find another name for IndexedMapping?
* [x] support indexing by another Teddy instance or an IndexedMapping.
* [x] we need a sequential type that exposes a dict interface but stores a list internally...
* ~~[ ] figure out a structure for POPO vs other possible impls~~
* [x] add tests
* [ ] figure out a name for different kinds of predicates
* [x] add support for implicit lambdas
* [x] support for a literal function that allows for accessing any constant in a dict that has special meaning for teddy.
