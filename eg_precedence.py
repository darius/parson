"""
Infix parsing with operator precedence (inefficient implementation).
"""

from parson import Grammar, recur, seclude, either, fail

def PrececedenceParser(primary_expr, table):
    return foldr(lambda make_expr, subexpr: make_expr(subexpr),
                 primary_expr,
                 table)

def LeftAssoc(*pairs):
    return lambda subexpr: \
        seclude(subexpr + alt([peg + subexpr + oper
                               for peg, oper in pairs]).star())

def RightAssoc(*pairs):
    return lambda subexpr: \
        recur(lambda expr:
                  seclude(subexpr + alt([peg + expr + oper
                                         for peg, oper in pairs]).maybe()))

def alt(pegs):
    return foldr(either, fail, pegs)

def foldr(f, z, xs):
    for x in reversed(xs):
        z = f(x, z)
    return z


# eg_calc.py example

from operator import *
from parson import delay

_    = delay(lambda: g._)
exp3 = delay(lambda: g.exp3)

exp1 = PrececedenceParser(exp3, [
        LeftAssoc(('*'+_, mul), ('//'+_, div), ('/'+_, truediv), ('%'+_, mod)),
        RightAssoc(('^'+_, pow)),
        ])

exps = PrececedenceParser(exp1, [
        LeftAssoc(('+'+_, add), ('-'+_, sub)),
        ])

g = Grammar(r"""
top  = _ :exps ~/./.

exp3 : '('_ :exps ')'_
     | '-'_ :exp1 :neg
     | /(\d+)/_ :int.

_    = /\s*/.
""")(**globals())

## g.top('42 *(5-3) + -2^2')
#. (80,)
## g.top('2^3^2')
#. (512,)
## g.top('5-3-1')
#. (1,)
## g.top('3//2')
#. (1,)
## g.top('3/2')
#. (1.5,)
