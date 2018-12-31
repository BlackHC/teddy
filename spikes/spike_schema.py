"""Spike Schema

Investigate what a schema could look like.reversed

Use dicts, sets, and tuples for specifying dataclasses, dicts and others.
Use lists for lists.

Need a special type for value-only dicts. Could use typing objects...

# Lessons

* A seperate Schema Type hierarchy based on dataclasses would be better.
* Need support for fixed-length arrays (to avoid optional value code paths)
* Support for typed tuples?
"""
import typing
import dataclasses
import prettyprinter
import functools

# TODO: support namedtuples? and callables?


# Requires schema to be canonical.
def schema_get(schema, key):
    if schema in (int, bool, str, float, None):
        return None
    if isinstance(schema, tuple):
        return object if key in schema else None
    if isinstance(schema, dict):
        return schema[key] if key in schema else None
    if isinstance(schema, list):
        return schema[0]
    if isinstance(schema, type(typing.Dict)):
        if schema.__origin__ == dict:
            vt = schema.__args__[1]
            return vt
        return object
    # Unknown type :(
    return object

def canonical_schema(schema):
    if schema in (int, bool, str, float, None):
        return schema
    if isinstance(schema, set):
        return tuple(schema)
    if isinstance(schema, tuple):
        return schema
    if isinstance(schema, dict):
        return {key: canonical_schema(value) for key, value in schema.items()}
    if isinstance(schema, list):
        return [canonical_schema(schema[0])] if schema else [object]
    if dataclasses.is_dataclass(schema):
        return {field.name: canonical_schema(field.type) for field in dataclasses.fields(schema)}
    if isinstance(schema, type(typing.List)):
        if schema.__origin__ == list:
            list_type = schema.__args__[0] or object
            return [canonical_schema(list_type)]
        if schema.__origin__ == dict:
            kt = canonical_schema(schema.__args__[0])
            vt = canonical_schema(schema.__args__[1])
            if vt == object and kt == object:
                return typing.Dict
            return typing.Dict[kt, vt]
        return object
    # Unknown type :(
    return object


class Schema:
    __slots__ = ('wrapped_schema')

    def __init__(self, wrapped_schema):
        self.wrapped_schema = wrapped_schema

    def __getattr__(self, key):
        return Schema(schema_get(self.wrapped_schema, key))

    def __getitem__(self, key):
        return Schema(schema_get(self.wrapped_schema, key))

    def __repr__(self):
        return prettyprinter.pretty_repr(self)


@prettyprinter.register_pretty(Schema)
def repr_schema(value, ctx):
    return prettyprinter.pretty_call(ctx, Schema, value.wrapped_schema)


def schema(definition: object):
    return Schema(canonical_schema(definition))


print(canonical_schema({'field1', 'field2'}))

schema1 = dict(params=typing.Dict[str, str], iterations=[dict(metrics=typing.Dict[str, float], choices=[int])])

pprint = functools.partial(prettyprinter.pprint, depth=4)
pprint(schema1)

pprint(canonical_schema(schema1))

schema1 = Schema(schema1)
pprint(schema1)
pprint(schema1.params)
pprint(schema1.iterations[0].metrics['loss'])


@dataclasses.dataclass
class TestDC:
    a: typing.Dict[str, str]
    b: typing.List[typing.Dict[str, int]]


pprint(canonical_schema(TestDC))
pprint(schema(TestDC).b[0]['hello'])


def validate_schema(schema, data):
    # TODO: needs to walk over datastructures and make sure the schema is compatible with the data.
    return False


def compute_schema(data):
    # TODO: Walk over all data entries and create an intersection type.
    return Schema(type(data))
