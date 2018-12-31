### Design thoughts on 12/26

LINQ and SQL can be thought of as implementing the following features:

* Filtering
* Aggregation
* Projection

Google uses the term MapReduce not mentioning filtering.

Python2 uses filter, map, reduce. Another useful function is zip.

One way to make these functions easier to use is to not require explicit lambda functions.

#### Q: Can we specify something like an XPath within a Python object?

Yes, we can wrap an object and provide specialized methods depending on its type and fields.

So we can provide a main function `teddy` that wraps objects and provides extensions/methods to
operate on them in a more 'natural' manner (which means whatever I find natural..).

Let's start with some example data:

```
stats: {
    'args': dict,
    'iterations': List[{
        'metrics': dict,
        'new_samples': list
        }]
} = ...

stats = teddy(stats)
```

`stats[...]` selects all fields and returns a view on stats
`stats['args']` or `stats.args` selects a single entry of a dict and returns a teddy wrapper of it.

To access the actual value, you have to use `stats.args.item`.

`stats.iterations[0, 1, 3]` returns a view on iterations 0, 1, and 3.
`stats.iterations[_index % 2 == 0]` returns all iterations with even index.
`stats.iterations[_.metrics.loss < 0.5]` returns all iterations with loss less than 0.5.
`stats.iterations[0, 1, 3].metrics[:].loss` returns all losses as a view.

The original structure is preserved:

```
{0: {metrics = {loss = 1}}, 1: {metrics = {loss = 0.5}}, 3 {metrics = {loss = 0.05}}}
```

#### Q: Is it necessary to preserve this structure?

Yes, if we want to assign/mutate the values in any way later.

We can iterate over all the losses if we want. Each entry should be a key value pair, where the key
specifies the path to the original item (one way or another).

#### Q: What's the difference between `...` and `:`?

`:` only really makes sense for lists. `...` can be more universal.

#### Q: What does this solve so far?

So far, this describes an API to select and filter. Selecting is the simplest form of a projection.

Other form of projection are not obvious just yet. Overall, only aggregation is missing, though.

#### Q: What other kinds of projection are there?

Selection is a projection that operates on the container. It projects the container to a different
form.

Reduction is another kind of projection that changes the type of element: from container to value.

Selecting multiple field could work as follows: `stats.iterations[:].metrics['loss', 'spf']`

#### What's the difference between `stats.iterations[:]` and `stats.iterations`?

The former operates on the view of all iterations and can expose the fields using member access. The latter exposes teddy helper functions.

`stats.iterations[:].metrics['loss', 'spf']` could also be written as `stats.iterations[:].metrics(loss=_.loss, spf=_.spf)` where `__call__` works on each metrics object as found from within `stats.iteration[:]`. The latter does not preserve original paths though.

So `apply/__call__` works on the object itself. `map` works on its items. `reduce` works on its items.

#### Q: What about aggregation?

`reduce` can handle aggregation. The more interesting question is about structural changes.

I need examples for this.

#### Q: What about joins?

We could use a structural `teddy.zip` that allows us to work on multiple structures in parallel.

`teddy.zip(structA, structB).intList.map(_[0] + _[1])` or
`teddy.zip(a=structA, b=structB).intList.map(_.a + _b)`

Ideally, this could also be written as `structA.intList + structB.intList`

#### Q: What about a simple tabular format?

```
@dataclass
class person:
    name: str
    surname: str
    age: int
    uid: str

persons: List[person] = ...
```

`teddy(persons).map({_.uid: _})[lookup_uid]` to look-up by an id.
`teddy(persons)[_.uid == lookup_id]` same

`teddy(persons).groupby('age')` yields a view of `Dict[int, List[person]]`.

#### Q: Can we also support GraphSQL-like queries?

We could try to match a structure using a dictionary representation with lambdas for filtering.

`stats.match(metrics=dict(loss: bool._(True))).metrics.loss`

#### Q: What about chained member access? They contradict the [...] narrative.

No, there is a difference.

`a_dict[...].a_field` accesses `a_field` in every value of `a_dict`.
`a_dict.a_field` accesses `a_field` in a `a_dict` itself.

`a_list.a_field` doesn't make sense though. `a_list[:].a_field` does.

Still, this means that for dicts and similar, there can be collisions between fields and extension methods provided by teddy.

#### We can try to guess field names for projections.

We need to create new namedtuple types during projections. We can inspect implicit lambdas to help with that.

#### How can we implement joins?

`teddy.map` and `teddy.zip` can implement structural joins.

What about field joins?

A join could be implemented using: `A.map(lambda x: B[_.id == x.id].map(_ | x).single)`
with `|` implementing a union of fields.

Problems:

* This requires an explicit lambda. implicit_lambda has no way to support such variable bindings.
* Two map calls whose order is arbitrary.
* Explicit handling of different join types by using single etc.

`teddy(a=A, b=B).join(_.a.id == _.b.id).map(_.a | _b)` could be a sensible formulation.

#### We don't have a schema, so we can't know the type of all items, and not every field might contain the same type

`[dict(), list()]` is entirely possible.

#### Teddy is immutable.

Yes.

## 12/28

### Revisiting [:] vs [...] vs nothing at all

We have a change to express more with additional indexing types.

Let's look at how arrays and tables are different and similar.
We can look at any xpath (xpath as expression path) in a data structure as multiindex.
Each element of the multiindex is a part of the chain.

So a.b.c.d == "[a,b,c,d]" with indices a, b, c, and d.

We could use [:] to change the order of these indices.

As we traverse lists and dicts, we only keep the dimensions we are not specifying specifically.

Specifically, we could use [:] to either flatten all previous indices or we could move that index to the front.

#### Dicts can be both records as well as lists with a primary key. Does this make a difference?

Not really. Lists just use integers as indices.

#### How could [...] and [:] be different?

One works on dicts and the other on lists.

Maybe, this would be to confusing.

But still: need operations to flatten the index and to change its order.

#### What would flattening mean:

One, it could mean merging indices together into a tuple and using that to store entries.
Another could mean chaining the elements of one dimension together, so the dimension is lost.

### Another take at indexing

`x: List[{a: List[int]}]`

`x[:].a` is `x_index -> a_value: List[int]`
`x.a[:]` is `a_index -> x_a_value: List[int]`

`x.a[:][:]` is `(a_index, x_index) -> int`
whereas
`x[:].a[:]` is `(x_index, a_index) -> int`

`x.a` == `x[:].a[:]`

So, we would have acknowledged indices and not acknowledged indices.

Now, what about more nesting:

`x: List[{a: List[{b: List[int]}]}]`

`x[:].a[:].b[:]` is `(x, a, b) -> int`
`x[:].a.b[:]` is `(x, b, a) -> int`
`x.a.b[:]` is `(b, x, a) -> int`
`x.a.b[:][:]` is `(b, a, x) -> int`?
`x.a[:].b` is `(a, x, b) -> int`
`x.a[:].b[:]` is `(a, b, x) -> int`

We have recovered all permutations.

`x[:].a[:].b` is `(x, a, b) -> int`
`x.a.b[:][:][:]` is `(b, a, x) -> int`?

#### What about nested arrays?

`x: List[List[List[int]]]`

`x[:][:][:]` is the only thing possible :(

Instead of dropping single-value indices we could preserve them.

#### How would this work with permutations though?

`x.a[0].b[:]` is `(b, x) -> int`

If we wanted to preserve single-value indices, we would want to preserve x, a, 0, and b.

`x.a[0].b[:] = {a: [{b: [{x: [ x[i_x].a[0].b[i_b]: int for i_x in x] }] for i_b in b}] }`

`x a 0 b:` -> `a 0 b x`

`a: b c 0 d:` -> `a c 0 d b`

`a: b_ c 0 d e_ f:` -> `a e_ f b_ c 0 d
`
(Insight: all of this is about manipulating indices. We never look at values.)

Problem: there is no way to do the same for dicts (not acknowledging an index)

Also, it is quite a costly operation.

#### `[...]` could be used for flattening.

Flattening would mean turning actual structure into tuples.

`a.b.c[...] -> Dict[(a, b, c), object]`

## 12/30

#### Multi-indexing

`a[[1,2,3]]` results in a sublist.
`a[(1,2,3)]` results in a dict or dataclass (depending on how many indices there are and if they are valid field names).
`a[{'name': 1, 'other_name': 2}]` results in a dataclass with the given fieldnames

`a[predicate]` results in a dict/dataclass
`a[[predicate]]` results in a sublist
`a[predicate1, predicate2]` results in a dict/dataclass of both `a[predicate1]` and `a[predicate2]`
(How do we pick the names though?)
`a[{'name': predicate1, 'othername':predicate2}]` results in a dataclass of dicts

NOTE: we need to allow indexing of dicts and dataclasses and namedtuples!
But then, how we disambiguate between an index and a key of type int?
.astuple? or(tuple)? would be an option!

---

Let's assume `swapi` contains all the data from the Star Wars APIs inside one big dict or DataClass.