"""
Abstract and concrete syntax of grammars.
"""

from structs import Struct as _S

class Call  (_S('name')): pass
class Empty (_S('')): pass
class Symbol(_S('text')): pass
class Either(_S('e1 e2')): pass
class Chain (_S('e1 e2')): pass
class Star  (_S('e1')): pass
class Action(_S('name')): pass

# TODO more efficient implementations:
def Maybe(e1):     return Either(e1, Empty())
def Plus(e1):      return Chain(e1, Star(e1))
def Plus2(e1, e2): return Chain(e1, Star(Chain(e2, e1)))
def Star2(e1, e2): return Maybe(Plus2(e1, e2))

metagrammar_text = r"""
'' rule* :end.

rule         :  name ':' exp '.' :hug.

exp          :  term ('|' exp :Either)?
             |                :Empty.

term         :  factor (term :Chain)?.
factor       :  primary ('**' primary :Star2
                        |'++' primary :Plus2
                        |'*'          :Star
                        |'+'          :Plus
                        |'?'          :Maybe
                        )?.

primary      :  qstring      :Symbol
             |  dqstring     :Symbol    # the same, just for now
             |  name         :Call
             |  ':' name     :Action
             |  ':' qstring  :Action
             |  '[' exp ']'         # dunno if we'll still want this for semantics
             |  '(' exp ')'.

name         :  /([A-Za-z_]\w*)/.

qstring     ~:  /'/ quoted_char* /'/ FNORD :join.
dqstring    ~:  '"' dquoted_char* '"' FNORD :join.

quoted_char ~:  /\\(.)/ | /([^'])/.
dquoted_char~:  /\\(.)/ | /([^"])/.

FNORD       ~:  whitespace?.
whitespace  ~:  /(?:\s|#.*)+/.
"""
