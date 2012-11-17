"""
Useless example grammar for testing.
"""

from parson import *

def meta_mk_feed(name):
    def fn(*args): return '%s(%s)' % (name, ' '.join(map(repr, args)))
    return label(feed(fn), lambda: 'feed(%s)' % name)
def meta_mk_rule_ref(name): return '<'+name+'>'  # XXX

def mk_empty(): return empty
def mk_literal(*cs): return literal(''.join(cs))
def mk_match(*cs): return match(''.join(cs))

meta_grammar = r"""
main            = _ rule+ /$/.
rule            = name '='_ nestpeg '.'_         :hug.
nestpeg         = peg :nest.

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
_               = /(?:\s|#[^\n]*\n?)*/.
"""

g = Grammar(meta_grammar)(**globals())
## for k, v in g.main(meta_grammar): print k, v
#. main nest(('<_>'+('<rule>'.plus()+match('$'))))
#. rule nest(('<name>'+(literal('=')+('<_>'+('<nestpeg>'+(literal('.')+('<_>'+feed(hug))))))))
#. nestpeg nest(('<peg>'+feed(nest)))
#. peg nest((('<term>'+(literal('|')+('<_>'+('<peg>'+feed(either)))))|('<term>'|feed(mk_empty))))
#. term nest((('<factor>'+('<term>'+feed(chain)))|'<factor>'))
#. factor nest(((literal('~')+('<_>'+('<factor>'+feed(invert))))|(('<primary>'+(literal('*')+('<_>'+feed(star))))|(('<primary>'+(literal('+')+('<_>'+feed(plus))))|(('<primary>'+(literal('?')+('<_>'+feed(maybe))))|'<primary>')))))
#. primary nest(((literal('(')+('<_>'+('<peg>'+(literal(')')+'<_>'))))|((literal('{')+('<_>'+('<peg>'+(literal('}')+('<_>'+feed(capture))))))|((match("'")+('<quoted_char>'.star()+(match("'")+('<_>'+feed(mk_literal)))))|((literal('/')+('<regex_char>'.star()+(literal('/')+('<_>'+feed(mk_match)))))|((literal(':')+('<_>'+('<name>'+feed(meta_mk_feed))))|('<name>'+feed(meta_mk_rule_ref))))))))
#. quoted_char nest((match('\\\\(.)')|match("([^'])")))
#. regex_char nest((match('(\\\\.)')|match('([^\\/])')))
#. name nest((match('([A-Za-z_]\\w*)')+'<_>'))
#. _ nest(match('(?:\\s|#[^\\n]*\\n?)*'))
#. 
