"""
Parse a string representation of a grammar.
"""

from re import escape
from parson import Peg, delay, \
    alt, catch, chop, chunk, empty, nest, seq, \
    invert, maybe, plus, star

class Grammar(object):
    def __init__(self, string, **actions):
        self.__dict__.update(parse_grammar(string, **actions))

def parse_grammar(string, **actions):

    mk_chop      = lambda name: chop(actions[name])
    mk_rule_ref  = lambda name: delay(lambda: rules[name])

    mk_empty     = lambda: empty
    mk_literal   = lambda *cs: Peg(escape(''.join(cs)))
    mk_match     = lambda *cs: Peg(''.join(cs))

    _              = Peg(r'(?:\s|#[^\n]*\n?)*')
    name           = Peg(r'([A-Za-z_]\w*)') +_

    regex_char     = Peg(r'(\\.)') | r"([^/])"
    quoted_char    = Peg(r'\\(.)') | r"([^'])"

    peg            = delay(lambda: 
                     term + r'\|' +_+ peg                    >> alt
                   | term
                   | empty                                   >> mk_empty)

    term           = delay(lambda:
                     factor + term                           >> seq
                   | factor)

    factor         = delay(lambda:
                     '!' +_+ factor                          >> invert
                   | primary + r'\*' +_                      >> star
                   | primary + r'\+' +_                      >> plus
                   | primary + r'\?' +_                      >> maybe
                   | primary)

    primary        = (r'\(' +_+ peg + r'\)' +_
                   | '{' +_+ peg + '}' +_                    >> catch
                   | "'" + quoted_char.star() + "'" +_       >> mk_literal
                   | '/' + regex_char.star() + '/' +_        >> mk_match
                   | ':' +_+ name                            >> mk_chop
                   | name                                    >> mk_rule_ref)

    rule           = name + '=' +_+ (peg>>nest) + r'\.' +_   >> chunk
    grammar        = _+ rule.plus() + '$'

    rules = dict(grammar(string))
    return rules


# Smoke test

nums = Grammar(r"""
# This is a comment.
main = nums /$/.  # So's this.

nums = num ',' nums
     | num
     | .

num  = /([0-9]+)/ :int.
""",
               int=int)
sum_nums = lambda s: sum(nums.main(s))

## sum_nums('10,30,43')
#. 83
## nums.nums('10,30,43')
#. (10, 30, 43)
## nums.nums('')
#. ()
## nums.num('10,30,43')
#. (10,)

## nums.main('10,30,43')
#. (10, 30, 43)
## nums.main.match('10,30,43 xxx')
