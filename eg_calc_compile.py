"""
After http://www.vpri.org/pdf/rn2010001_programm.pdf
"""

from parson import Grammar

def assign(v, exp): return exp(0) + ['sw r0, ' + v]

def ld_const(value): return lambda s: ['lc r%d, %d' % (s, value)]
def ld_var(name):    return lambda s: ['lw r%d, %s' % (s, name)]

def add(exp1, exp2): return lambda s: (exp1(s) + exp2(s+1)
                                       + ['add r%d, r%d, r%d' % (s, s+1, s)])
def mul(exp1, exp2): return lambda s: (exp1(s) + exp2(s+1)
                                       + ['mul r%d, r%d, r%d' % (s, s+1, s)])

g = Grammar(r"""
top   :  _ stmt :end.

stmt  :  ident ':='_ exp0   :assign.

exp0  :  exp1 ('+'_ exp1    :add)*.
exp1  :  exp2 ('*'_ exp2    :mul)*.

exp2  :  '('_ exp0 ')'_
      |  /(\d+)/_ :int      :ld_const
      |  ident              :ld_var.

ident =  /([A-Za-z]+)/_.
_     =  /\s*/.
""")(**globals())

## for line in g.top('v := 42 * (5+3) + 2*2')[0]: print line
#. lc r0, 42
#. lc r1, 5
#. lc r2, 3
#. add r1, r2, r1
#. mul r0, r1, r0
#. lc r1, 2
#. lc r2, 2
#. mul r1, r2, r1
#. add r0, r1, r0
#. sw r0, v
