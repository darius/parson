"""
The customary calculator example.
"""

import operator
from parson import Grammar

calc = Grammar(r"""  exp0 :end.

exp0  :  exp1 ( '+'  exp1 :add
              | '-'  exp1 :sub )*.
exp1  :  exp2 ( '*'  exp2 :mul
              | '//' exp2 :div
              | '/'  exp2 :truediv
              | '%'  exp2 :mod )*.
exp2  :  exp3 ( '^'  exp2 :pow )?.

exp3  :  '(' exp0 ')'
      |  '-' exp1 :neg
      |  /(\d+)/  :int.

FNORD~:  /\s*/.

""").bind(operator).expecting_one_result()

## calc('42 * (5-3) + -2^2')
#. 80
## calc('2^3^2')
#. 512
## calc('5-3-1')
#. 1
## calc('3//2')
#. 1
## calc('3/2')
#. 1.5
