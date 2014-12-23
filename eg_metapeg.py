"""
Useless example grammar for testing.
"""

from parson import *

def meta_mk_feed(name):
    def fn(*args): return '%s(%s)' % (name, ' '.join(map(repr, args)))
    return label(feed(fn), ':'+name)
def meta_mk_rule_ref(name): return '<'+name+'>'  # XXX

def mk_empty(): return empty
def mk_literal(*cs): return literal(''.join(cs))
def mk_match(*cs): return match(''.join(cs))

meta_grammar = r"""
main         :  _ rule+ ~/./.
rule         :  name ('='_   pe
                     |':'_ [pe :seclude])
                '.'_                           :hug.

pe           :  term ('|'_ pe :either)?
             |                                 :mk_empty.
term         :  factor (term :chain)?.
factor       :  '~'_ factor                    :invert
             |  primary ('*'_ :star
                        |'+'_ :plus
                        |'?'_ :maybe)?.
primary      :  '('_ pe ')'_
             |  '['_ pe ']'_                   :seclude
             |  '{'_ pe '}'_                   :capture
             |  /'/ quoted_char* /'/_          :mk_literal
             |  '/' regex_char*  '/'_          :mk_match
             |  ':'_ name                      :meta_mk_feed
             |  name                           :meta_mk_rule_ref.

quoted_char  :  /\\(.)/ | /([^'])/.
regex_char   :  /(\\.)/ | /([^\/])/.

name         :  /([A-Za-z_]\w*)/ _.
_            :  /(?:\s|#.*)*/.
"""

g = Grammar(meta_grammar)(**globals())
## for k, v in g.main(meta_grammar): print k, v
#. main [('<_>' (('<rule>')+ ~(/./)))]
#. rule [('<name>' (((literal('=') ('<_>' '<pe>'))|(literal(':') ('<_>' [('<pe>' :seclude)]))) (literal('.') ('<_>' :hug))))]
#. pe [(('<term>' ((literal('|') ('<_>' ('<pe>' :either))))?)|:mk_empty)]
#. term [('<factor>' (('<term>' :chain))?)]
#. factor [((literal('~') ('<_>' ('<factor>' :invert)))|('<primary>' (((literal('*') ('<_>' :star))|((literal('+') ('<_>' :plus))|(literal('?') ('<_>' :maybe)))))?))]
#. primary [((literal('(') ('<_>' ('<pe>' (literal(')') '<_>'))))|((literal('[') ('<_>' ('<pe>' (literal(']') ('<_>' :seclude)))))|((literal('{') ('<_>' ('<pe>' (literal('}') ('<_>' :capture)))))|((/'/ (('<quoted_char>')* (/'/ ('<_>' :mk_literal))))|((literal('/') (('<regex_char>')* (literal('/') ('<_>' :mk_match))))|((literal(':') ('<_>' ('<name>' :meta_mk_feed)))|('<name>' :meta_mk_rule_ref)))))))]
#. quoted_char [(/\\(.)/|/([^'])/)]
#. regex_char [(/(\\.)/|/([^\/])/)]
#. name [(/([A-Za-z_]\w*)/ '<_>')]
#. _ [/(?:\s|#.*)*/]
