"""
Parse a regular expression and generate the strings it matches.
Generator from
http://www.udacity.com/wiki/CS212%20Unit%203%20Code?course=cs212#regex_generatorpy
http://forums.udacity.com/questions/5008809/unit3-18-startx-paramater-on-genseq-is-a-hack#cs212
and in embryo
https://github.com/darius/halp/blob/master/examples/learn-the-hell-out-of-regular-expressions/whats_a_regex_soln.py
"""

from parson import Grammar, join

def generate(regex, Ns):
    "Return the strings matching regex whose length is in Ns."
    return sorted(parser.regex(regex)[0](Ns),
                  key=lambda s: (len(s), s))

def literal(s):   return lambda Ns: set([s]) if len(s) in Ns else null
def either(x, y): return lambda Ns: x(Ns) | y(Ns)
def plus(x):      return chain(x, star(x))
def star(x):      return lambda Ns: optional(chain(nonempty(x), star(x)))(Ns)
def nonempty(x):  return lambda Ns: x(Ns - set([0]))
def oneof(chars): return lambda Ns: set(chars) if 1 in Ns else null
def chain(x, y):  return lambda Ns: genseq(x, y, Ns)
def optional(x):  return either(empty(), x)
def dot():        return oneof('?')  # (Could be more, for lots more output.)
def empty():      return literal('')

null = frozenset([])

def genseq(x, y, Ns):
    """Return the set of matches to xy whose total length is in Ns. We
    ask y only for lengths that are remainders after an x-match in
    0..max(Ns). (And we call neither x nor y if there are no Ns.)"""
    if not Ns:
        return null
    xmatches = x(set(range(max(Ns)+1)))
    Ns_x = set(len(m) for m in xmatches)
    Ns_y = set(n-m for n in Ns for m in Ns_x if n-m >= 0)
    ymatches = y(Ns_y)
    return set(m1+m2 for m1 in xmatches for m2 in ymatches if len(m1+m2) in Ns)

grammar = Grammar(r"""
regex    :  exp !/./.
exp      :  term ('|' exp     :either)*
         |                    :empty.
term     :  factor (term      :chain)*.
factor   :  primary (  '*'    :star
                     | '+'    :plus
                     | '?'    :optional
                    )?.
primary  :  '(' exp ')'
         |  '[' char* ']'     :join :oneof
         |  '.'               :dot
         |  /\\(.)/           :literal
         |  /([^.()*+?|[\]])/ :literal.
char     :  /\\(.)/
         |  /([^\]])/.
""")
parser = grammar(**globals())

## generate('.+', range(5))
#. ['?', '??', '???', '????']
## generate('a[xy]+z()*|c.hi', range(5))
#. ['axz', 'ayz', 'axxz', 'axyz', 'ayxz', 'ayyz', 'c?hi']
## generate('(Chloe|Yvette), a( precocious)? (toddler|writer)', range(28))
#. ['Chloe, a writer', 'Chloe, a toddler', 'Yvette, a writer', 'Yvette, a toddler', 'Chloe, a precocious writer', 'Chloe, a precocious toddler', 'Yvette, a precocious writer']

## parser.regex.attempt('{"hi"](')
