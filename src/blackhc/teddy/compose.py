"""Composition of functions.

`compose_naive` and `compose` have similar mean runtime, however `compose_naive` needs to access
the list of functions, so can suffer from more cache misses.
"""
import typing
import functools


def compose_naive(*funcs):
    r_funcs = list(reversed(funcs))

    def composition(x):
        for f in r_funcs:
            x = f(x)
        return x

    return composition


def compose(*funcs: typing.List[typing.Callable[[typing.Any], typing.Any]]):
    """Returns `lambda x: funcs[0](funcs[1](...(x)))`."""
    code = f"""
def composed_func_builder():
{chr(10).join(f'    func{i} = funcs[{i}]' for i in range(len(funcs)))}
    return lambda x: {''.join(f'func{i}(' for i in range(len(funcs)))}x{')'*len(funcs)}

composed_func=composed_func_builder()
    """
    namespace = {}
    exec(code, dict(funcs=funcs, __builtins__={}), namespace)
    return namespace['composed_func']
