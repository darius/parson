"""
Tiny example of 'compiling'.
"""

from parson import Grammar, alter

g = Grammar(r"""
top   :  _ stmt* :end.

stmt  :  ident '='_ exp0 ';'_ :assign.

exp0  :  exp1 ('+'_ exp1      :'add')*.
exp1  :  exp2 ('*'_ exp2      :'mul')*.

exp2  :  '('_ exp0 ')'_
      |  /(\d+)/_
      |  ident                :'fetch'.

ident :  /([A-Za-z]+)/_.
_     :  /\s*/.
""")(assign=alter(lambda name, *exp: exp + (name, 'store')))

## print ' '.join(g.top('v = 42 * (5+3) + 2*2; v = v + 1;'))
#. 42 5 3 add mul 2 2 mul add v store v fetch 1 add v store
