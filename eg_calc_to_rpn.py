"""
Tiny example of 'compiling'.
"""

from parson import Grammar, alter

g = Grammar(r"""  stmt* :end.

stmt   :  ident '=' exp0 ';'  :assign.

exp0   :  exp1 ('+' exp1      :'add')*.
exp1   :  exp2 ('*' exp2      :'mul')*.

exp2   :  '(' exp0 ')'
       |  /(\d+)/
       |  ident               :'fetch'.

ident  :  /([A-Za-z]+)/.

FNORD ~:  /\s*/.
""")(assign=alter(lambda name, *exp: exp + (name, 'store')))

## print ' '.join(g('v = 42 * (5+3) + 2*2; v = v + 1;'))
#. 42 5 3 add mul 2 2 mul add v store v fetch 1 add v store
