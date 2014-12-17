"""
Useless example grammar for testing.
"""

from parson import *

def meta_mk_feed(name):
    def fn(*args): return '%s(%s)' % (name, ' '.join(map(repr, args)))
    return label(feed(fn), 'feed(%s)', name)
def meta_mk_rule_ref(name): return '<'+name+'>'  # XXX

def mk_empty(): return empty
def mk_literal(*cs): return literal(''.join(cs))
def mk_match(*cs): return match(''.join(cs))

meta_grammar = r"""
main          ::= _ rule+ ~/./.
rule          ::= name ('='_   pe
                       |'::='_ [pe :seclude])
                  '.'_                           :hug.

pe            ::= term ('|'_ pe :either)?
               |                                 :mk_empty.
term          ::= factor (term :chain)?.
factor        ::= '~'_ factor                    :invert
               |  primary ('*'_ :star
                          |'+'_ :plus
                          |'?'_ :maybe)?.
primary       ::= '('_ pe ')'_
               |  '['_ pe ']'_                   :seclude
               |  '{'_ pe '}'_                   :capture
               |  /'/ quoted_char* /'/_          :mk_literal
               |  '/' regex_char*  '/'_          :mk_match
               |  ':'_ name                      :meta_mk_feed
               |  name                           :meta_mk_rule_ref.

quoted_char   ::= /\\(.)/ | /([^'])/.
regex_char    ::= /(\\.)/ | /([^\/])/.

name          ::= /([A-Za-z_]\w*)/ _.
_             ::= /(?:\s|#.*)*/.
"""

g = Grammar(meta_grammar)(**globals())
## for k, v in g.main(meta_grammar): print k, v
#. main seclude(('<_>'+('<rule>'.plus()+~(match('.')))))
#. rule seclude(('<name>'+(((literal('=')+('<_>'+'<pe>'))|(literal('::=')+('<_>'+seclude(('<pe>'+feed(seclude))))))+(literal('.')+('<_>'+feed(hug))))))
#. pe seclude((('<term>'+(literal('|')+('<_>'+('<pe>'+feed(either)))).maybe())|feed(mk_empty)))
#. term seclude(('<factor>'+('<term>'+feed(chain)).maybe()))
#. factor seclude(((literal('~')+('<_>'+('<factor>'+feed(invert))))|('<primary>'+((literal('*')+('<_>'+feed(star)))|((literal('+')+('<_>'+feed(plus)))|(literal('?')+('<_>'+feed(maybe))))).maybe())))
#. primary seclude(((literal('(')+('<_>'+('<pe>'+(literal(')')+'<_>'))))|((literal('[')+('<_>'+('<pe>'+(literal(']')+('<_>'+feed(seclude))))))|((literal('{')+('<_>'+('<pe>'+(literal('}')+('<_>'+feed(capture))))))|((match("'")+('<quoted_char>'.star()+(match("'")+('<_>'+feed(mk_literal)))))|((literal('/')+('<regex_char>'.star()+(literal('/')+('<_>'+feed(mk_match)))))|((literal(':')+('<_>'+('<name>'+feed(meta_mk_feed))))|('<name>'+feed(meta_mk_rule_ref)))))))))
#. quoted_char seclude((match('\\\\(.)')|match("([^'])")))
#. regex_char seclude((match('(\\\\.)')|match('([^\\/])')))
#. name seclude((match('([A-Za-z_]\\w*)')+'<_>'))
#. _ seclude(match('(?:\\s|#.*)*'))
