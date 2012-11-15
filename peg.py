"""
Parse a string representation of a grammar.
"""

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

    mk_chop      = lambda name: chop(actions[name])
    mk_rule_ref  = lambda name: delay(lambda: rules[name])

    mk_empty     = lambda: empty
    mk_literal   = lambda *cs: Peg(escape(''.join(cs)))
    mk_match     = lambda *cs: Peg(''.join(cs))

    _              = Peg(r'\s*')  # TODO add comments
    name           = Peg(r'([A-Za-z_]\w*)') +_

    regex_char     = Peg(r'(\\.)') | r"([^/])"
    quoted_char    = Peg(r'\\(.)') | r"([^'])"

    peg            = delay(lambda: 
                     term + (r'\|' +_+ term).star()          >> fold_alt
                   | empty                                   >> mk_empty)

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
