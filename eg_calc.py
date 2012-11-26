"""
Testing out tree parsing.
"""

from operator import add, sub
from parson import anyone, capture, delay, nest, one_of, one_that

end = ~anyone

def match(p, x): return (p + end)([x])

def an_instance(typ): return one_that(lambda x: isinstance(x, typ))

def capture1(p): return capture(p) >> (lambda x: x[0]) # Ouch
var = capture1(anyone)
## (var + var)(eg)
#. ('+', 2)

calc = delay(lambda:
               nest(one_of('+') + calc + calc + end) >> add
             | nest(one_of('-') + calc + calc + end) >> sub
             | capture1(an_instance(int)))

eg = ['+', 2, 3]
## match(calc, eg)
#. (5,)

eg2 = ['+', ['-', 2, 4], 3]
## match(calc, eg2)
#. (1,)


# Exercise: transforming trees with generic walks

flatten1 = delay(lambda:
                   nest(one_of('+') + flatten1.star() + end)
                 | capture1(an_instance(int)))

## match(flatten1, ['+', ['+', ['+', 1, ['+', 2]]]])
#. (1, 2)

# Figure 2.7 in the OMeta thesis, more or less:

def walk(p, q=capture1(an_instance(int))):
    expr = (  nest(one_of('+') + p.star() + end) >> tag('+')
            | nest(one_of('-') + p.star() + end) >> tag('-')
            | q)
    return expr

def tag(constant):
    return lambda *args: (constant,) + args

flatten2 = delay(lambda:
                   nest(one_of('+') + flatten2 + end)
                 | nest(one_of('+') + inside.star() + end) >> tag('+')
                 | walk(flatten2))
inside   = delay(lambda:
                   nest(one_of('+') + inside.star() + end)
                 | flatten2)

## match(flatten2, ['+', ['+', ['+', 1, ['+', 2], ['+', 3, 4]]]])
#. (('+', 1, 2, 3, 4),)
