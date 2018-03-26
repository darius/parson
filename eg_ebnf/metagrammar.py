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

metagrammar_text = r"""
'' rule* :end.

rule         :  name ':' exp '.' :hug.

exp          :  term ('|' exp :Either)?
             |                :Empty.

term         :  factor (term :Chain)?.
factor       :  primary ('*' :Star)?.

primary      :  qstring  :Symbol
             |  name     :Call
             |  '(' exp ')'.

name         :  /([A-Za-z_]\w*)/.

qstring     ~:  /'/ quoted_char* /'/ FNORD :join.
quoted_char ~:  /\\(.)/ | /([^'])/.

FNORD       ~:  whitespace?.
whitespace  ~:  /(?:\s|#.*)+/.
"""
