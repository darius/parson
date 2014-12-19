"""
A bunch of small examples, some of them from the LPEG documentation.
Crudely converted from Peglet. TODO: make them nicer.
"""

from parson import Grammar, Unparsable, hug, join, position

parse_words = Grammar(r'words ::= /\W*(\w+)/ words | .')()

# The equivalent re.split() would return extra '' results first and last:
## parse_words.words('"Hi, there", he said.')
#. ('Hi', 'there', 'he', 'said')

def Tag(label):
    return lambda *parts: (label,) + parts

name = Grammar(r"""
name    ::= title first middle last.
title   ::= title_ :Title _ |.
title_  ::= /(Dr|Mr|Ms|Mrs|St)[.]?/ | /(Pope(?:ss)?)/.
first   ::= /([A-Za-z]+)/ :First _.
middle  ::= middle_ :Middle _ |.
middle_ ::= /([A-Z])[.]/ | /([A-Za-z]+)/.
last    ::= /([A-Za-z]+)/ :Last.
_       ::= /\s+/.
""")(Title  = Tag('title'),
     First  = Tag('first'),
     Middle = Tag('middle'),
     Last   = Tag('last'))
## name.name('Popess Darius Q. Bacon')
#. (('title', 'Popess'), ('first', 'Darius'), ('middle', 'Q'), ('last', 'Bacon'))

ichbins = Grammar(r"""
main     ::=  _ sexp.

sexp     ::=  /\\(.)/         _ :lit_char
          |   '"' qchars '"'  _ :join
          |   symchars        _ :join
          |   /'/ _ sexp        :quote
          |   '(' _ sexps ')' _ :hug.

sexps    ::=  sexp sexps
          |  .

qchars   ::=  /\\(.)/ qchars
          |   /([^"])/ qchars
          |   .

symchars ::=  symchar symchars
          |   symchar.
symchar  ::=  /([^\s\\"'()])/.

_        ::=  /\s*/.
""")(lit_char = ord,
     join     = join,
     quote    = lambda x: ('quote', x),
     hug      = hug)

## ichbins.sexps('() (hey)')
#. ((), ('hey',))

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
allS ::= S ~/./.

S    ::= /a/ B
      |  /b/ A
      |  .

A    ::= /a/ S
      |  /b/ A A.

B    ::= /b/ S
      |  /a/ B B.
""")()

## as_and_bs.allS("abaabbbbaa")
#. ()

nums = Grammar(r"""
allnums ::= nums ~/./.

nums    ::= num ',' nums
         |  num
         |  .

num     ::= /(\d+)/ :int.
""")(int=int)
sum_nums = lambda s: sum(nums.allnums(s))

## sum_nums('10,30,43')
#. 83

one_word = Grammar(r"word ::= /\w+/ :position.")(position=position)

## one_word.word('hello')
#. (5,)
## one_word.word('hello there')
#. (5,)
## one_word.word.attempt(' ')

namevalues = Grammar(r"""
list   ::= _ pairs ~/./.
pairs  ::= pair pairs
        |  .
pair   ::= name '=' _ name /[,;]?/ _   :hug.
name   ::= /(\w+)/ _.
_      ::= /\s*/.
""")(**globals())
namevalues_dict = lambda s: dict(namevalues.list(s))
## namevalues_dict("a=b, c = hi; next = pi")
#. {'a': 'b', 'c': 'hi', 'next': 'pi'}

# Splitting a string. But with lpeg it's parametric over a pattern p.
# NB this assumes p doesn't match '', and that it doesn't capture.

splitting = Grammar(r"""
split  ::= p split
        |  chunk :join split
        |  .
chunk  ::= p
        |  /(.)/ chunk.
p      ::= /\s/.
""")(**globals())
## splitting.split('hello a world  is    nice    ')
#. ('hello', 'a', 'world', 'is', 'nice')

# Searching for a pattern: also parameterized by p.
# (skipped)

balanced_parens = Grammar(r"""
bal  ::=  '(' cs ')'.
cs   ::=  c cs
      |   .
c    ::=  /[^()]/
      |   bal.
""")()

## balanced_parens.bal.attempt('()')
#. ()
## balanced_parens.bal.attempt('(()')

# gsub: another parameterized one

gsub = lambda text, replacement: ''.join(Grammar(r"""
gsub ::=  p gsub
      |   /(.)/ gsub
      |   .
p    ::=  /WHEE/ :replace.
""")(replace=lambda: replacement).gsub(text))

## gsub('hi there WHEEWHEE to you WHEEEE', 'GLARG')
#. 'hi there GLARGGLARG to you GLARGEE'

csv = Grammar(r"""
record ::=   field fields ~/./.
fields ::=   ',' field fields
        |    .

field  ::=   '"' qchars /"\s*/ :join
        |    /([^,"\n]*)/.

qchars ::=   qchar qchars
        |    .
qchar  ::=   /([^"])/
        |    '""' :dquote.
""")(join = join,
     dquote = lambda: '"')

## csv.record('')
#. ('',)
## csv.record('""')
#. ('',)
## csv.record("""hi,there,,"this,isa""test"   """)
#. ('hi', 'there', '', 'this,isa"test')


## Grammar('x ::= .')().x('')
#. ()

def p(grammar, rule, text):
    parse = getattr(Grammar(grammar)(**globals()),
                    rule)
    try:
        return parse(text)
    except Unparsable, e:
        return e

metagrammar = r"""
grammar       ::=  _ rule+.
rule          ::=  name '=' _ expr '.' _    :make_rule.
expr          ::=  term.
term          ::=  factors ':' _ name       :reduce_
               |   factors.
factors       ::=  factor factors           :seq
               |                            :empty.
factor        ::=  /'((?:\\.|[^'])*)'/ _    :literal
               |   name                     :rule_ref.
name          ::=  /(\w+)/ _.
_             ::=  /\s*/.
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
allbalanced ::=  _ bal ~/./.
_           ::=  /\s*/.
bal         ::=  '(' _ bal ')' _ :hug bal
             |   /(\w+)/ _
             |  .
"""
## p(bal, 'allbalanced', '(x) y')
#. (('x',), 'y')
## p(bal, 'allbalanced', 'x y')
#. Unparsable(allbalanced, 'x ', 'y')

curl = r"""
one_expr ::=  _ expr ~/./.
_        ::=  /\s*/.
expr     ::=  '{' _ exprs '}' _ :hug
          |   /([^{}\s]+)/ _.
exprs    ::=  expr exprs
          |   .
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
hi ::= /this/ /is/
       /a/ /rule/
    |  /or/ /this/.
"""

## p(multiline_rules, 'hi', "thisisarule")
#. ()
## p(multiline_rules, 'hi', "orthis")
#. ()
## p(multiline_rules, 'hi', "thisisnot")
#. Unparsable(hi, 'thisis', 'not')
