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

# TODO: optimizer example
