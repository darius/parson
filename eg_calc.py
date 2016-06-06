"""
The customary calculator example.
"""

import operator
from parson import Grammar

g = Grammar(r"""
top   :  _ exp0 !/./.

exp0  :  exp1 (  '+'_  exp1 :add
               | '-'_  exp1 :sub)*.
exp1  :  exp2 (  '*'_  exp2 :mul
               | '//'_ exp2 :div
               | '/'_  exp2 :truediv
               | '%'_  exp2 :mod)*.
exp2  :  exp3 (  '^'_  exp2 :pow)?.

exp3  :  '('_ exp0 ')'_
      |  '-'_ exp1 :neg
      |  /(\d+)/_ :int.

_     =  /\s*/.
""").bind(operator)

## g.top('42 * (5-3) + -2^2')
#. (80,)
## g.top('2^3^2')
#. (512,)
## g.top('5-3-1')
#. (1,)
## g.top('3//2')
#. (1,)
## g.top('3/2')
#. (1.5,)
