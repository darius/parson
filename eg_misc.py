"""
A bunch of small examples, some of them from the LPEG documentation.
Crudely converted from Peglet. TODO: make them nicer.
"""

from parson import Grammar, Unparsable, exceptionally

parse_words = Grammar(r'words  :  /\W*(\w+)/ words | .')()

# The equivalent re.split() would return extra '' results first and last:
## parse_words.words('"Hi, there", he said.')
#. ('Hi', 'there', 'he', 'said')

class Tagger(dict):
    def __missing__(self, key):
        return lambda *parts: (key,) + parts

name = Grammar(r"""
name    :  title first middle last.
title   :  (/(Dr|Mr|Ms|Mrs|St)[.]?/ | /(Pope(?:ss)?)/) _ :Title |.
first   :  /([A-Za-z]+)/ _ :First.
middle  :  (/([A-Z])[.]/ | /([A-Za-z]+)/) _ :Middle |.
last    :  /([A-Za-z]+)/ :Last.
_       :  /\s+/.
""").bind(Tagger())

## name.name('Popess Darius Q. Bacon')
#. (('Title', 'Popess'), ('First', 'Darius'), ('Middle', 'Q'), ('Last', 'Bacon'))

ichbins = Grammar(r"""
main     :  _ sexp.

sexp     :  /\\(.)/         _ :lit_char
         |  '"' qchar* '"'  _ :join
         |  symchar+        _ :join
         |  /'/ _ sexp        :quote
         |  '(' _ sexp* ')' _ :hug.

qchar    :  /\\(.)/
         |  /([^"])/.

symchar  :  /([^\s\\"'()])/.

_        :  /\s*/.
""")(lit_char = ord,
     quote    = lambda x: ('quote', x))

## ichbins.sexp('(hey)')
#. (('hey',),)

## ichbins.main('hi')
#. ('hi',)
## ichbins.main(r"""(hi '(john mccarthy) \c )""")
#. (('hi', ('quote', ('john', 'mccarthy')), 99),)
## ichbins.main(r""" ""  """)
#. ('',)
## ichbins.main(r""" "hey"  """)
#. ('hey',)

# From http://www.inf.puc-rio.br/~roberto/lpeg/

as_and_bs = Grammar(r"""
allS  :  S !/./.

S     :  'a' B
      |  'b' A
      |  .

A     :  'a' S
      |  'b' A A.

B     :  'b' S
      |  'a' B B.
""")()

## as_and_bs.allS("abaabbbbaa")
#. ()

nums = Grammar(r"""
allnums  :  nums? !/./.
nums     :  num (',' num)*.
num      :  /(\d+)/ :int.
""")()
sum_nums = lambda s: sum(nums.allnums(s))

## sum_nums('10,30,43')
#. 83

one_word = Grammar(r"word  :  /\w+/ :position.")()

## one_word.word('hello')
#. (5,)
## one_word.word('hello there')
#. (5,)
## one_word.word.attempt(' ')

namevalues = Grammar(r"""
list  :  _ pair* !/./.
pair  :  name '=' _ name /[,;]?/ _   :hug.
name  :  /(\w+)/ _.
_     :  /\s*/.
""")(**globals())
namevalues_dict = lambda s: dict(namevalues.list(s))
## namevalues_dict("a=b, c = hi; next = pi")
#. {'a': 'b', 'c': 'hi', 'next': 'pi'}

# Splitting a string. TODO: But with lpeg it's parametric over a pattern p.
# NB this assumes p doesn't match '', and that it doesn't capture.

splitting = Grammar(r"""
split  :  (p | chunk :join) split | .  # XXX why not a *?
chunk  :  p
       |  /(.)/ chunk.
p      :  /\s/.
""")(**globals())
## splitting.split('hello a world  is    nice    ')
#. ('hello', 'a', 'world', 'is', 'nice')
## splitting.chunk('hello a world  is    nice    ')
#. ('h', 'e', 'l', 'l', 'o')

# Searching for a pattern: also parameterized by p.
# (skipped)

balanced_parens = Grammar(r"""
bal  :  '(' c* ')'.
c    :  /[^()]/
     |  bal.
""")()

## balanced_parens.bal.attempt('()')
#. ()
## balanced_parens.bal.attempt('(()')

# gsub: another parameterized one

gsub = lambda text, pattern, replacement: ''.join(Grammar(r"""
gsub:  (p | /(.)/) gsub
    |  .
p:     :pattern :replace.
""")(pattern=pattern, replace=lambda: replacement).gsub(text))

## gsub('hi there WHEEWHEE to you WHEEEE', 'WHEE', 'GLARG')
#. 'hi there GLARGGLARG to you GLARGEE'

csv = Grammar(r"""
record  :  field (',' field)* !/./.

field   :  '"' qchar* /"\s*/ :join
        |  /([^,"\n]*)/.

qchar   :  /([^"])/
        |  '""' :'"'.
""")()

## csv.record('')
#. ('',)
## csv.record('""')
#. ('',)
## csv.record("""hi,there,,"this,isa""test"   """)
#. ('hi', 'there', '', 'this,isa"test')


## Grammar('x  :  .')().x('')
#. ()

def p(grammar, rule, text):
    parse = getattr(Grammar(grammar)(**globals()),
                    rule)
    try:
        return parse(text)
    except Unparsable, e:
        return e

metagrammar = r"""
grammar  :  _ rule+.
rule     :  name '=' _ expr '.' _    :make_rule.
expr     :  term ('|' expr           :alt)*.
term     :  factors (':' _ name      :reduce_)?.
factors  :  factor factors           :seq
         |                           :empty.
factor   :  /'((?:\\.|[^'])*)'/ _    :literal
         |  name                     :rule_ref.
name     :  /(\w+)/ _.
_        :  /\s*/.
"""

def make_rule(name, expr): return '%s: %s' % (name, expr)
def alt(e1, e2):           return '%s/%s' % (e1, e2)
def reduce_(e, name):      return '%s =>%s' % (e, name)
def seq(e1, *e2):          return '%s+%s' % ((e1,) + e2) if e2 else e1
def empty():               return '<>'
def literal(regex):        return '/%s/' % regex
def rule_ref(name):        return '<%s>' % name

## p(metagrammar, 'grammar', ' hello = bargle. goodbye = hey there.aloha=.')
#. ('hello: <bargle>+<>', 'goodbye: <hey>+<there>+<>', 'aloha: <>')
## p(metagrammar, 'grammar', ' hello arg = bargle.')
#. Unparsable(grammar, ' hello ', 'arg = bargle.')
## p(metagrammar, 'term', "'goodbye' world")
#. ('/goodbye/+<world>+<>',)

bal = r"""
allbalanced  :  _ bal !/./.
_            :  /\s*/.
bal          :  '(' _ bal ')' _ :hug bal
             |  /(\w+)/ _
             |  .
"""
## p(bal, 'allbalanced', '(x) y')
#. (('x',), 'y')
## p(bal, 'allbalanced', 'x y')
#. Unparsable(allbalanced, 'x ', 'y')

curl = r"""
one_expr  :  _ expr !/./.
_         :  /\s*/.
expr      :  '{' _ expr* '}' _ :hug
          |  /([^{}\s]+)/ _.
"""
## p(curl, 'one_expr', '')
#. Unparsable(one_expr, '', '')
## p(curl, 'one_expr', '{}')
#. ((),)
## p(curl, 'one_expr', 'hi')
#. ('hi',)
## p(curl, 'one_expr', '{hi {there} {{}}}')
#. (('hi', ('there',), ((),)),)

multiline_rules = r"""
hi  :  /this/ /is/
       /a/ /rule/
    |  /or/ /this/.
"""

## p(multiline_rules, 'hi', "thisisarule")
#. ()
## p(multiline_rules, 'hi', "orthis")
#. ()
## p(multiline_rules, 'hi', "thisisnot")
#. Unparsable(hi, 'thisis', 'not')

paras = Grammar(r"""
paras: para* _ !/./.
para:  _ word+ (/\n\n/ | !/./) :hug.
word:  /(\S+)/ _.
_:     (!/\n\n/ /\s/)*.
""")()

eg = r"""  hi  there   hey
how are you?
  fine.

thanks.

ok then."""

## exceptionally(lambda: paras.paras(eg))
#. (('hi', 'there', 'hey', 'how', 'are', 'you?', 'fine.'), ('thanks.',), ('ok', 'then.'))
