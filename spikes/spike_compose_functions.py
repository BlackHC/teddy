""" Spike

How can we write a function that composes a sequence of functions together?

"""
import functools
import timeit
import pytest


def compose_0(*funcs):
    r_funcs = list(reversed(funcs))

    def composition(x):
        for f in r_funcs:
            x = f(x)
        return x
    return composition


def compose_1(*funcs):
    return functools.reduce(lambda right, left: lambda x: left(right(x)), reversed(funcs), lambda x: x)

def compose_2(*funcs):
    code = f"lambda x: {''.join(f'funcs[{i}](' for i in range(len(funcs)))}x" + ')'*len(funcs)
    return eval(code, dict(funcs=funcs))

def compose_3(*funcs):
    code = f"lambda x: {''.join(f'func{i}(' for i in range(len(funcs)))}x" + ')'*len(funcs)
    return eval(code, {f'func{i}': funcs[i] for i in range(len(funcs))})

def compose_4(*funcs):
    code = f"""
def composed_func_builder():
{chr(10).join(f'    func{i} = funcs[{i}]' for i in range(len(funcs)))}
    return lambda x: {''.join(f'func{i}(' for i in range(len(funcs)))}x{')'*len(funcs)}

composed_func=composed_func_builder()
    """
    locals = {}
    exec(code, dict(funcs=funcs, __builtins__={}), locals)
    return locals['composed_func']

ex5_1 = lambda x: x+1
ex5_2 = lambda x: x*2
ex5_3 = lambda x: x+5


ex=[
    ('compose_0', compose_0(lambda x: x+1, lambda x: x*2, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5)),
    ('compose_1', compose_1(lambda x: x+1, lambda x: x*2, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5)),
    ('compose_2', compose_2(lambda x: x+1, lambda x: x*2, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5)),
    ('compose_3', compose_3(lambda x: x+1, lambda x: x*2, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5)),
    ('compose_4', compose_4(lambda x: x+1, lambda x: x*2, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5, lambda x: x+5)),
    ('fused_calls', lambda x: ex5_1(ex5_2(ex5_3(ex5_3(ex5_3(ex5_3(ex5_3(ex5_3(ex5_3(x)))))))))),
    ('fused_expr', lambda x: ((((((((x+5)+5)+5)+5)+5)+5)*2)+1))
]

@pytest.mark.parametrize(('name', 'func'), ex)
def test_benchmark(name, func, benchmark):
    benchmark(func, 5)
