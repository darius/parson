"""
Parse a string representation of a grammar.
"""

from re import escape
from parson import *

class Struct(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def Grammar(string):
    rules, items = parse_grammar(string)
    def bind(**subs):           # subs = substitutions
        for rule, f in items:
            rules[rule] = f(subs)
        return Struct(**rules)
    return bind

def parse_grammar(string):

    rules = {}
    refs = set()

    def mk_rule_ref(name):
        refs.add(name)
        ref = delay(lambda: rules[name])
        return lambda subs: ref

    def lift(peg_op):
        return lambda *lifted: lambda subs: peg_op(*[f(subs) for f in lifted])

    unquote    = lambda name: lambda subs: Peg(subs[name])

    mk_literal = lambda *cs: lambda subs: Peg(escape(''.join(cs)))
    mk_match   = lambda *cs: lambda subs: Peg(''.join(cs))

    _              = Peg(r'(?:\s|#[^\n]*\n?)*')
    name           = Peg(r'([A-Za-z_]\w*)') +_

    regex_char     = Peg(r'(\\.)') | r"([^/])"
    quoted_char    = Peg(r'\\(.)') | r"([^'])"

    peg            = delay(lambda: 
                     term + r'\|' +_+ peg               >> lift(alt)
                   | term
                   | empty                              >> lift(lambda: empty))

    term           = delay(lambda:
                     factor + term                      >> lift(seq)
                   | factor)

    factor         = delay(lambda:
                     '!' +_+ factor                     >> lift(invert)
                   | primary + r'\*' +_                 >> lift(star)
                   | primary + r'\+' +_                 >> lift(plus)
                   | primary + r'\?' +_                 >> lift(maybe)
                   | primary)

    primary        = (r'\(' +_+ peg + r'\)' +_
                   | '{' +_+ peg + '}' +_               >> lift(catch)
                   | "'" + quoted_char.star() + "'" +_  >> mk_literal
                   | '/' + regex_char.star() + '/' +_   >> mk_match
                   | ':' +_+ name                       >> unquote
                   | name                               >> mk_rule_ref)

    rule           = name + '=' +_+ (peg>>lift(nest)) + r'\.' +_ >> hug
    grammar        = _+ rule.plus() + '$'

    items = grammar(string)
    lhses = [L for L, R in items]
    undefined = sorted(refs - set(lhses))
    if undefined: raise Exception("Undefined rules: %s" % ', '.join(undefined))
    dups = sorted(L for L in set(lhses) if 1 != lhses.count(L))
    if dups: raise Exception("Multiply-defined rules: %s" % ', '.join(dups))
    return rules, items


# Smoke test

## bad1 = Grammar(r"a = . b = a. a = .")()
#. Traceback (most recent call last):
#.   File "peg.py", line 13, in Grammar
#.     rules, items = parse_grammar(string)
#.   File "peg.py", line 75, in parse_grammar
#.     if dups: raise Exception("Multiply-defined rules: %s" % ', '.join(dups))
#. Exception: Multiply-defined rules: a

## bad2 = Grammar(r"a = b|c|d. c = .")()
#. Traceback (most recent call last):
#.   File "peg.py", line 13, in Grammar
#.     rules, items = parse_grammar(string)
#.   File "peg.py", line 73, in parse_grammar
#.     if undefined: raise Exception("Undefined rules: %s" % ', '.join(undefined))
#. Exception: Undefined rules: b, d

nums = Grammar(r"""
# This is a comment.
main = nums /$/.  # So's this.

nums = num ',' nums
     | num
     | .

num  = /([0-9]+)/ :int.
""")(int=int)
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


gsub_grammar = Grammar(r"""
gsub = sub gsub | /(.)/ gsub | .
sub = :p :replace.
""")
def gsub(text, p, replacement):
    g = gsub_grammar(p=p, replace=lambda: replacement)
    return ''.join(g.gsub(text))
## gsub('hi there WHEEWHEE to you WHEEEE', Peg('WHEE'), 'GLARG')
#. 'hi there GLARGGLARG to you GLARGEE'
