"""
Exploring making tree parsing central.
"""

import re


# Some derived combinators

def invert(p):    return cond(p, fail, succeed)
def either(p, q): return cond(p, p, q)
def both(p, q):   return cond(p, q, fail)

def feed(p, f): return alter(p, lambda *vals: (f(*vals),))

def maybe(p):   return either(p, succeed)
def plus(p):    return chain(p, star(p))
def star(p):    return recur(lambda p_star: maybe(chain(p, p_star)))

def recur(fn):
    p = delay(lambda: fn(p))
    return p


# Peg objects

def Peg(x):
    if isinstance(x, _Peg):           return x
#    if isinstance(x, (str, unicode)): return literal(x)
    if callable(x):                   return satisfying(x)
    raise ValueError("Not a Peg", x)

class _Peg(object):
    def __init__(self, run):
        self.run = run

    def __call__(self, sequence):
        for vals, _ in self.run(sequence):
            return vals
        return None

    def __add__(self, other):  return chain(self, Peg(other))
    def __radd__(self, other): return chain(Peg(other), self)
    def __or__(self, other):   return either(self, Peg(other))
    def __ror__(self, other):  return either(Peg(other), self)

    __rshift__ = feed
    __invert__ = invert
    maybe = maybe
    plus = plus
    star = star


# Basic combinators

nil = ['nil']

fail    = _Peg(lambda s: [])
succeed = _Peg(lambda s: [((), s)])

def cond(p, q, r):
    def run(s):
        pv = p.run(s)
        choice = q if pv else r
        if choice is p: return pv # (an optimization)
        else: return choice.run(s)
    return _Peg(run)

def satisfying(ok):
    "Eat a subject s when ok(s), producing (s,)."
    return _Peg(lambda s: [((s,), nil)] if ok(s) else [])

def chain(p, q):
    return _Peg(lambda s: [(pvals + qvals, qnub)
                           for pvals, pnub in p.run(s)
                           if pnub is not nil
                           for qvals, qnub in q.run(pnub)])

def alter(p, f):
    return _Peg(lambda s: [(f(*vals), nub)
                           for vals, nub in p.run(s)])

def delay(thunk):
    def run(s):
        q.run = Peg(thunk()).run
        return q.run(s)
    q = _Peg(run)
    return q

def item(p):
    "Eat the first item of a sequence, iff p matches it."
    def run(s):
        try: first = s[0]
        except IndexError: return []
        except TypeError: return []
        except KeyError: return []
        return [(vals, s[1:]) for vals, _ in p.run(first)]
    return _Peg(run)

def match(regex, flags=0):
    compiled = re.compile(regex, flags)
    return _Peg(lambda s: [(m.groups(), s[m.end():])
                           for m in [compiled.match(s)] if m])

def capture(p):
    def run(s):
        for vals, nub in p.run(s):
            # XXX use the position change instead, once we're tracking that:
            if s is not nil and nub is not nil:
                i = len(s) - len(nub)
                if s[i:] == nub:
                    return [((s[:i],), nub)]
            raise Exception("Bad capture")
        return []
    return _Peg(run)

## capture(match('h..') + match('.'))('hi there')
#. ('hi t',)
## capture(item(anything) + item(anything))([3])
## capture(item(anything) + item(anything))([3, 1])
#. ([3, 1],)


# More derived combinators

## startswith('hi')('hi there')
#. ()

def startswith(s): return match(re.escape(s))

anything = satisfying(lambda s: True)
def literal(c): return drop(satisfying(lambda s: c == s))
def drop(p): return alter(p, lambda *vals: ())

end = invert(item(anything))   # Hmmm

def an_instance(type_):
    return satisfying(lambda x: isinstance(x, type_))

def alt(*ps):
    if not ps: return fail
    if not ps[1:]: return ps[0]
    return either(ps[0], alt(*ps[1:]))

def items(*ps):
    if not ps: return end
    return chain(item(ps[0]), items(*ps[1:]))

def seq(*ps):
    if not ps: return succeed
    return chain(ps[0], seq(*ps[1:]))

give = lambda c: feed(succeed, lambda: c)


# Examples

from operator import *

## fail(42)
## anything(42)
#. (42,)
## chain(item(literal(5)), item(literal(0)))([5, 0, 2])
#. ()
## an_instance(int)(42)
#. (42,)

calc = delay(lambda:
       alt(feed(items(literal('+'), calc, calc), add),
           feed(items(literal('-'), calc, calc), sub),
           an_instance(int)))

## calc(42)
#. (42,)
## calc(['-', 3, 1])
#. (2,)
## calc(['+', ['-', 2, 1], 3])
#. (4,)

singleton = lambda v: (v,)
cat = lambda *lists: sum(lists, ())
flatten1 = delay(lambda:
           alt(seq(item(literal('+')), star(item(flatten1)), end),
               an_instance(int)))

## flatten1(['+', ['+', ['+', 1, ['+', 2]]]])
#. (1, 2)
## flatten1(42)
#. (42,)
## flatten1(['+'])
#. ()
## flatten1(['+', 42])
#. (42,)
## flatten1(['+', 42, 43])
#. (42, 43)

## chain(item(literal('+')), anything)(['+', 42])
#. ([42],)

## star(item(anything))([1,2,3])
#. (1, 2, 3)

## star(match('hi() '))('hi hi hi there')
#. ('', '', '')
