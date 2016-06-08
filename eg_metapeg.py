"""
Useless example grammar for testing.
"""

from parson import *

def meta_mk_feed(name):
    def fn(*args): return '%s(%s)' % (name, ' '.join(map(repr, args)))
    return label(feed(fn), ':'+name)
def meta_mk_rule_ref(name): return '<'+name+'>'  # XXX

def mk_empty(): return empty

def fnordify(peg): return peg #+ '<FNORD>'

meta_grammar = r""" rule+ :end | anon :end.

anon         :  :None :'' [:'' :literal fnordly pe :chain] :hug  ('.' rule*)?.

rule         :  name {'~'?} ('='   pe
                            |':'~whitespace [pe :seclude])
                '.'                        :hug.

pe           :  term ('|' pe :either)?
             |                             :mk_empty.
term         :  factor (term :chain)?.
factor       :  '!' factor                 :invert
             |  primary ('**' primary :star
                        |'++' primary :plus
                        |'*' :star
                        |'+' :plus
                        |'?' :maybe)?.
primary      :  '(' pe ')'
             |  '[' pe ']'                 :seclude
             |  '{' pe '}'                 :capture
             |  qstring  :literal fnordly
             |  dqstring :literal fnordly
             |  regex    :match   fnordly
             |  ':'~( name                 :meta_mk_feed
                    | qstring              :push)
             |  name                       :meta_mk_rule_ref.

fnordly      =  ('~' | :fnordify).

name         :  /([A-Za-z_]\w*)/.

FNORD       ~:  whitespace?.
whitespace  ~:  /(?:\s|#.*)+/.

qstring     ~:  /'/  quoted_char* /'/ FNORD :join.
dqstring    ~:  '"' dquoted_char* '"' FNORD :join.
regex       ~:  '/'   regex_char* '/' FNORD :join.

quoted_char ~:  /\\(.)/ | /([^'])/.
dquoted_char~:  /\\(.)/ | /([^"])/.
regex_char  ~:  /(\\.)/ | /([^\/])/.
"""

metapeg = Grammar(meta_grammar)(**globals())
## for k, af, v in metapeg(meta_grammar): print k, af, v
#. None  (literal('') ((('<rule>')+ :end)|('<anon>' :end)))
#. anon  [(:None (push('') ([(push('') (:literal ('<fnordly>' ('<pe>' :chain))))] (:hug ((literal('.') ('<rule>')*))?))))]
#. rule  [('<name>' (capture((literal('~'))?) (((literal('=') '<pe>')|(literal(':') ('<whitespace>' [('<pe>' :seclude)]))) (literal('.') :hug))))]
#. pe  [(('<term>' ((literal('|') ('<pe>' :either)))?)|:mk_empty)]
#. term  [('<factor>' (('<term>' :chain))?)]
#. factor  [((literal('!') ('<factor>' :invert))|('<primary>' (((literal('**') ('<primary>' :star))|((literal('++') ('<primary>' :plus))|((literal('*') :star)|((literal('+') :plus)|(literal('?') :maybe))))))?))]
#. primary  [((literal('(') ('<pe>' literal(')')))|((literal('[') ('<pe>' (literal(']') :seclude)))|((literal('{') ('<pe>' (literal('}') :capture)))|(('<qstring>' (:literal '<fnordly>'))|(('<dqstring>' (:literal '<fnordly>'))|(('<regex>' (:match '<fnordly>'))|((literal(':') (('<name>' :meta_mk_feed)|('<qstring>' :push)))|('<name>' :meta_mk_rule_ref))))))))]
#. fnordly  (literal('~')|:fnordify)
#. name  [/([A-Za-z_]\w*)/]
#. FNORD ~ [('<whitespace>')?]
#. whitespace ~ [/(?:\s|#.*)+/]
#. qstring ~ [(/'/ (('<quoted_char>')* (/'/ ('<FNORD>' :join))))]
#. dqstring ~ [(literal('"') (('<dquoted_char>')* (literal('"') ('<FNORD>' :join))))]
#. regex ~ [(literal('/') (('<regex_char>')* (literal('/') ('<FNORD>' :join))))]
#. quoted_char ~ [(/\\(.)/|/([^'])/)]
#. dquoted_char ~ [(/\\(.)/|/([^"])/)]
#. regex_char ~ [(/(\\.)/|/([^\/])/)]
