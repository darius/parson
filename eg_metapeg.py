"""
Useless example grammar for testing.
"""

from parson import *

def meta_mk_feed(name):
    def fn(*args): return '%s(%s)' % (name, ' '.join(map(repr, args)))
    return feed(fn)
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
#. rule nest(('<name>'+(match('\\=')+('<_>'+('<nestpeg>'+(match('\\.')+('<_>'+feed(fn))))))))
#. nestpeg nest(('<peg>'+feed(fn)))
#. peg nest((('<term>'+(match('\\|')+('<_>'+('<peg>'+feed(fn)))))|('<term>'|feed(fn))))
#. term nest((('<factor>'+('<term>'+feed(fn)))|'<factor>'))
#. factor nest(((match('\\~')+('<_>'+('<factor>'+feed(fn))))|(('<primary>'+(match('\\*')+('<_>'+feed(fn))))|(('<primary>'+(match('\\+')+('<_>'+feed(fn))))|(('<primary>'+(match('\\?')+('<_>'+feed(fn))))|'<primary>')))))
#. primary nest(((match('\\(')+('<_>'+('<peg>'+(match('\\)')+'<_>'))))|((match('\\{')+('<_>'+('<peg>'+(match('\\}')+('<_>'+feed(fn))))))|((match("'")+('<quoted_char>'.star()+(match("'")+('<_>'+feed(fn)))))|((match('\\/')+('<regex_char>'.star()+(match('\\/')+('<_>'+feed(fn)))))|((match('\\:')+('<_>'+('<name>'+feed(fn))))|('<name>'+feed(fn))))))))
#. quoted_char nest((match('\\\\(.)')|match("([^'])")))
#. regex_char nest((match('(\\\\.)')|match('([^\\/])')))
#. name nest((match('([A-Za-z_]\\w*)')+'<_>'))
#. _ nest(match('(?:\\s|#[^\\n]*\\n?)*'))
#. 
