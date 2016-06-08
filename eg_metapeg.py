"""
Useless example grammar for testing.
"""

from parson import *

def meta_mk_feed(name):
    def fn(*args): return '%s(%s)' % (name, ' '.join(map(repr, args)))
    return label(feed(fn), ':'+name)
def meta_mk_rule_ref(name): return '<'+name+'>'  # XXX

def mk_empty(): return empty

meta_grammar = r""" _ (rule+ :end | anon :end).

anon         :  :None pe :hug ('.'_ rule*)?.
rule         :  name ('='_   pe
                     |':' whitespace [pe :seclude])
                '.'_                           :hug.

pe           :  term ('|'_ pe :either)?
             |                                 :mk_empty.
term         :  factor (term :chain)?.
factor       :  '!'_ factor                    :invert
             |  primary ('**'_ primary :star
                        |'++'_ primary :plus
                        |'*'_ :star
                        |'+'_ :plus
                        |'?'_ :maybe)?.
primary      :  '('_ pe ')'_
             |  '['_ pe ']'_                   :seclude
             |  '{'_ pe '}'_                   :capture
             |  qstring                        :literal
             |  '/' regex_char*  '/'_          :join :match
             |  ':'(name                       :meta_mk_feed
                   |qstring                    :push)
             |  name                           :meta_mk_rule_ref.

qstring      :  /'/ quoted_char* /'/_          :join.

quoted_char  :  /\\(.)/ | /([^'])/.
regex_char   :  /(\\.)/ | /([^\/])/.

name         :  /([A-Za-z_]\w*)/ _.
_            :  whitespace?.
whitespace   :  /(?:\s|#.*)+/.
"""

metapeg = Grammar(meta_grammar)(**globals())
## for k, v in metapeg(meta_grammar): print k, v
#. None ('<_>' ((('<rule>')+ :end)|('<anon>' :end)))
#. anon [(:None ('<pe>' (:hug ((literal('.') ('<_>' ('<rule>')*)))?)))]
#. rule [('<name>' (((literal('=') ('<_>' '<pe>'))|(literal(':') ('<whitespace>' [('<pe>' :seclude)]))) (literal('.') ('<_>' :hug))))]
#. pe [(('<term>' ((literal('|') ('<_>' ('<pe>' :either))))?)|:mk_empty)]
#. term [('<factor>' (('<term>' :chain))?)]
#. factor [((literal('!') ('<_>' ('<factor>' :invert)))|('<primary>' (((literal('**') ('<_>' ('<primary>' :star)))|((literal('++') ('<_>' ('<primary>' :plus)))|((literal('*') ('<_>' :star))|((literal('+') ('<_>' :plus))|(literal('?') ('<_>' :maybe)))))))?))]
#. primary [((literal('(') ('<_>' ('<pe>' (literal(')') '<_>'))))|((literal('[') ('<_>' ('<pe>' (literal(']') ('<_>' :seclude)))))|((literal('{') ('<_>' ('<pe>' (literal('}') ('<_>' :capture)))))|(('<qstring>' :literal)|((literal('/') (('<regex_char>')* (literal('/') ('<_>' (:join :match)))))|((literal(':') (('<name>' :meta_mk_feed)|('<qstring>' :push)))|('<name>' :meta_mk_rule_ref)))))))]
#. qstring [(/'/ (('<quoted_char>')* (/'/ ('<_>' :join))))]
#. quoted_char [(/\\(.)/|/([^'])/)]
#. regex_char [(/(\\.)/|/([^\/])/)]
#. name [(/([A-Za-z_]\w*)/ '<_>')]
#. _ [('<whitespace>')?]
#. whitespace [/(?:\s|#.*)+/]
