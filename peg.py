"""
Parse a string representation of a grammar.
"""

import sys; sys.setrecursionlimit(3000) # XXX
from re import escape
from parson import Peg, delay, \
    alt, catch, chop, chunk, empty, fail, nest, seq, \
    invert, maybe, plus, star

def fold_seq(*factors): return foldr(seq, empty, factors)
def fold_alt(*terms):   return foldr(alt, fail, terms)

def foldr(f, z, xs):
    for x in reversed(xs):
        z = f(x, z)
    return z

def Grammar(string, **actions):

    rules = {}

    mk_literal   = lambda *cs: Peg(escape(''.join(cs)))
    mk_match     = lambda *cs: Peg(''.join(cs))
    mk_chop      = lambda name: chop(actions[name])
    mk_rule_ref  = lambda name: delay(lambda: rules[name])

    _              = Peg(r'\s*')  # TODO add comments
    name           = Peg(r'([A-Za-z_]\w*)') +_

    regex_char     = Peg(r'(\\.)') | r"([^/])"
    quoted_char    = Peg(r'\\(.)') | r"([^'])"

    peg            = delay(lambda: 
                     term + (r'\|' +_+ term).star()          >> fold_alt
                   | empty                                   >> (lambda: empty))

    primary        = (r'\(' +_+ peg + r'\)' +_
                   | '{' +_+ peg + '}' +_                    >> catch
                   | "'" + quoted_char.star() + "'" +_       >> mk_literal
                   | '/' + regex_char.star() + '/' +_        >> mk_match
                   | ':' +_+ name                            >> mk_chop
                   | name                                    >> mk_rule_ref)

    factor         = delay(lambda:
                     '!' +_+ factor                          >> invert
                   | primary + r'\*' +_                      >> star
                   | primary + r'\+' +_                      >> plus
                   | primary + r'\?' +_                      >> maybe
                   | primary)

    term           = factor.plus()                           >> fold_seq

    rule           = name + '=' +_+ (peg>>nest) + r'\.' +_   >> chunk
    grammar        = _+ rule.plus() + '$'

    rules = dict(grammar(string))
    return rules['main']  # XXX use first rule instead

meta_grammar = r"""
main            = _ rule+ /$/                    :id.
rule            = name '='_ peg '.'_             :id.

peg             = term ('|'_ term)*              :id
                |                                :id.
term            = factor+                        :id.
factor          = '!'_ factor                    :id
                | primary '*'_                   :id
                | primary '+'_                   :id
                | primary '?'_                   :id
                | primary.
primary         = '('_ peg ')'_
                | '{'_ peg '}'_                  :id
                | /'/ quoted_char* /'/_          :id
                | '/' regex_char*  '/'_          :id
                | ':'_ name                      :id
                | name                           :id.

quoted_char     = /\\(.)/ | /([^'])/.
regex_char      = /(\\.)/ | /([^\/])/.

name            = /([A-Za-z_]\w*)/ _.
_               = /(?:\s|#[^\n]*\n?)*/.
"""

g = Grammar(meta_grammar, id=lambda *xs: xs)

nums = Grammar(r"""
main = nums /$/.

nums = num ',' nums
     | num.

num  = /([0-9]+)/ :int.
""",
               int=int)
sum_nums = lambda s: sum(nums(s))

# XXX in nums:
#      | .

## sum_nums('10,30,43')
#. 83
