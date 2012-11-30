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
main            = _ rule+ /$/.
rule            = name '='_ secludepeg '.'_      :hug.
secludepeg      = peg :seclude.

peg             = term '|'_ peg                  :either
                | term
                |                                :mk_empty.
term            = factor term                    :chain
                | factor.
factor          = '~'_ factor                    :invert
                | primary '*'_                   :star
                | primary '+'_                   :plus
                | primary '?'_                   :maybe
                | primary.
primary         = '('_ peg ')'_
                | '{'_ peg '}'_                  :capture
                | /'/ quoted_char* /'/_          :mk_literal
                | '/' regex_char*  '/'_          :mk_match
                | ':'_ name                      :meta_mk_feed
                | name                           :meta_mk_rule_ref.

quoted_char     = /\\(.)/ | /([^'])/.
regex_char      = /(\\.)/ | /([^\/])/.

name            = /([A-Za-z_]\w*)/ _.
_               = /(?:\s|#.*)*/.
"""

g = Grammar(meta_grammar)(**globals())
## for k, v in g.main(meta_grammar): print k, v
#. main seclude(('<_>'+('<rule>'.plus()+match('$'))))
#. rule seclude(('<name>'+(literal('=')+('<_>'+('<secludepeg>'+(literal('.')+('<_>'+feed(hug))))))))
#. secludepeg seclude(('<peg>'+feed(seclude)))
#. peg seclude((('<term>'+(literal('|')+('<_>'+('<peg>'+feed(either)))))|('<term>'|feed(mk_empty))))
#. term seclude((('<factor>'+('<term>'+feed(chain)))|'<factor>'))
#. factor seclude(((literal('~')+('<_>'+('<factor>'+feed(invert))))|(('<primary>'+(literal('*')+('<_>'+feed(star))))|(('<primary>'+(literal('+')+('<_>'+feed(plus))))|(('<primary>'+(literal('?')+('<_>'+feed(maybe))))|'<primary>')))))
#. primary seclude(((literal('(')+('<_>'+('<peg>'+(literal(')')+'<_>'))))|((literal('{')+('<_>'+('<peg>'+(literal('}')+('<_>'+feed(capture))))))|((match("'")+('<quoted_char>'.star()+(match("'")+('<_>'+feed(mk_literal)))))|((literal('/')+('<regex_char>'.star()+(literal('/')+('<_>'+feed(mk_match)))))|((literal(':')+('<_>'+('<name>'+feed(meta_mk_feed))))|('<name>'+feed(meta_mk_rule_ref))))))))
#. quoted_char seclude((match('\\\\(.)')|match("([^'])")))
#. regex_char seclude((match('(\\\\.)')|match('([^\\/])')))
#. name seclude((match('([A-Za-z_]\\w*)')+'<_>'))
#. _ seclude(match('(?:\\s|#.*)*'))
#. 
