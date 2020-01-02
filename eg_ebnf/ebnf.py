"""
Parse a grammar,
check that it's LL(1),
transform to make its LL(1) nature explicit,
and recognize inputs according to the grammar.
TODO semantic actions
"""

from collections import Counter
from structs import Struct, Visitor
import parson
import metagrammar

zet = frozenset
empty_zet = zet()

metaparser = parson.Grammar(metagrammar.metagrammar_text).bind(metagrammar)

class Grammar(object):
    def __init__(self, text, actions=None):
        self.actions = actions
        pairs = metaparser(text)
        self.nonterminals = tuple(pair[0] for pair in pairs)
        self.rules = dict(pairs)
        self.ana = analyze(self)
        self.errors = []
        check(self)
        self.directed = {name: directify(rule, self.ana)
                         for name, rule in self.rules.items()}

    def show_analysis(self):
        for r in self.nonterminals:
            nul = self.ana.nullable(self.rules[r])
            fst = self.ana.firsts(self.rules[r])
            print '%-8s %-6s %s' % (r, nul, ' '.join(sorted(s.text for s in fst)))

    def lexer_symbols(self):
        return empty_zet.union(*map(collect_symbols, self.directed.values()))

    def parse(self, tokens, start='start'):
        parsing = Parsing(self.directed, self.actions, tokens)
        parsing.calls.append(start)
        try:
            #print 'start', self.directed[start]
            parsing(self.directed[start])
        except SyntaxError, e:
            print e, "at %d" % parsing.i
        else:
            print 'ok at', parsing.i, parsing.stack[0]

class CollectSymbols(Visitor):
    def Symbol(self, t):  return zet([t])
    def Branch(self, t):  return self(t.default).union(*[zet(kinds) | self(alt)
                                                         for kinds,alt in t.cases])
    def Chain(self, t):   return self(t.e1) | self(t.e2)
    def Loop(self, t):    return zet(t.firsts) | self(t.body)
    def default(self, t): return empty_zet
collect_symbols = CollectSymbols()


# Check that the grammar is well-formed and LL(1)

def check(grammar):
    dups = find_duplicates(grammar.nonterminals)
    if dups:
        grammar.errors.append("Duplicate definitions: %r" % dups)
    def error(plaint):
        message = '%s: %s' % (name, plaint)
        if message not in grammar.errors:
            grammar.errors.append(message)
    for name in grammar.nonterminals:
        Checker(grammar.ana, error)(grammar.rules[name], name)

def find_duplicates(xs):
    counts = Counter(xs)
    return sorted(x for x,n in counts.items() if 1 < n)

class Checker(Visitor):
    def __init__(self, ana, error):
        self.ana = ana
        self.error = error

    def Either(self, t, context):
        ts = flatten(t)
        if 1 < len(ts):
            if 1 < sum(map(self.ana.nullable, ts)):
                self.error("Multiple defaults")
            first_sets = map(self.ana.firsts, ts)
            overlap = find_duplicates(token for fs in first_sets for token in fs)
            if overlap:
                self.error("Branches overlap: %r" % overlap)
        for leaf in ts:
            self(leaf, context)

    def Chain(self, t, context):
        self(t.e1, context)
        self(t.e2, context if self.ana.nullable(t.e1) else None)

    def Star(self, t, context):
        if self.ana.nullable(t.e1):
            self.error("Unproductive loop")
        self(t.e1, context)

    def Call(self, t, context):
        if t.name == context:
            self.error("Left recursion")

    def default(self, t, context):
        pass


# Grammar analysis

r"""
OK, what's LL(1)?
The first-sets of each either-branch must be disjoint.
Also, the argument of a Star must be non-nullable.

firsts(Empty)            = {}                      # or make it {epsilon}?
firsts(Symbol(t))        = {t}
firsts(Call(r))          = firsts(rules[r])        # to closure
firsts(Either(e1, e2))   = firsts(e1) | firsts(e2)
firsts(Chain(e1, e2))    = firsts(e1) | (firsts(e2) if nullable(e1) else {})
firsts(Star(e1))         = firsts(e1)              # | {epsilon} if we go that way

nullable(Empty)          = Yes
nullable(Symbol(_))      = No
nullable(Call(r))        = nullable(rules[r])      # to closure
nullable(Either(e1, e2)) = nullable(e1) | nullable(e2)
nullable(Chain(e1, e2))  = nullable(e1) & nullable(e2)
nullable(Star(_))        = Yes

Can we do this with one function instead of two? E.g. using {epsilon} as above?
In fact, couldn't EOF be a valid token to switch on? I don't think I'm accounting
for that ("follow sets", iirc).
"""

Analysis = Struct('nullable firsts')

def analyze(grammar):
    nul = Nullable(compute_nullables(grammar.rules))
    fst = First(nul, compute_firsts(grammar.rules, nul))
    return Analysis(nul, fst)

def fixpoint(rules, initial, make_visitor):
    bounds = {name: initial for name in rules}
    while True:
        prev_state = dict(bounds)
        visitor = make_visitor(bounds)
        for name in rules:
            bounds[name] = visitor(rules[name])
        if prev_state == bounds:
            return bounds

def compute_nullables(rules):
    return fixpoint(rules, True, Nullable)

class Nullable(Visitor):
    def __init__(self, nul):
        self.nul = nul

    def Empty(self, t):  return True
    def Symbol(self, t): return False
    def Call(self, t):   return self.nul[t.name]
    def Either(self, t): return self(t.e1) | self(t.e2)
    def Chain(self, t):  return self(t.e1) & self(t.e2)
    def Star(self, t):   return True
    def Action(self, t): return True

def compute_firsts(rules, nul):
    return fixpoint(rules, empty_zet, lambda fst: First(nul, fst)) # TODO better naming

class First(Visitor):
    def __init__(self, nul, fst):
        self.nul = nul
        self.fst = fst

    def Empty(self, t):  return empty_zet
    def Symbol(self, t): return zet([t])
    def Call(self, t):   return self.fst[t.name]
    def Either(self, t): return self(t.e1) | self(t.e2)
    def Chain(self, t):  return self(t.e1) | (self(t.e2) if self.nul(t.e1) else empty_zet)
    def Star(self, t):   return self(t.e1)
    def Action(self, t): return empty_zet


# 'Directed' form
# Embed the result of the LL(1) analysis where it'll be needed by
# an interpreter or compiler of the grammar.

# firsts is the first-set of body.
class Loop(Struct('firsts body')): pass

# Each case is a pair (kinds, t) where kinds is the first-set of
# t. Every Branch has a catch-all, 'default'. It's a Fail unless the
# source grammar supplies a nullable case. (This catch-all could be
# avoided if we could know that the cases are exhaustive.)
class Branch(Struct('cases default')): pass

# possibles is a zet of the tokens that would have made the parse not
# fail at this point.
class Fail(Struct('possibles')): pass

class Directify(Visitor):
    def Either(self, t, ana):  return gen_branch(flatten(t), ana)
    def Chain(self, t, ana):   return metagrammar.Chain(self(t.e1, ana),
                                                        self(t.e2, ana))
    def Star(self, t, ana):    return Loop(ana.firsts(t.e1), self(t.e1, ana))
    def default(self, t, ana): return t
directify = Directify()

class Flatten(Visitor):
    def Either(self, t):  return self(t.e1) + self(t.e2)
    def default(self, t): return (t,)
flatten = Flatten()

# XXX I think my logic is faulty: it should be able to handle an optional
# without committing to blindly matching epsilon even if a first-set token
# matches (which seems to be what's happening now).
def gen_branch(ts, ana):
    cases = []
    defaults = []
    for t in ts:
        directed = directify(t, ana)
        if ana.nullable(t):
            defaults.append(directed)
        else:
            firsts = ana.firsts(t)
            if firsts: cases.append((firsts, directed))

    if not defaults:
        if not cases:       return Fail(empty_zet)
        if len(cases) == 1: return cases[0][1]
        possibles = zet().union(*map(ana.firsts, ts))
        defaults = [Fail(possibles)]
    # We always just use the first default, because we only require
    # this to work for an LL(1) grammar.
    if not cases: return defaults[0]
    return Branch(cases, defaults[0])


# Parse by interpretation
# (TODO maybe drop this in favor of vm.py; or drop that instead)

class SyntaxError(Exception): pass

class Parsing(Visitor):
    def __init__(self, rules, actions, tokens):
        self.rules = rules
        self.actions = actions
        self.tokens = list(tokens) # Although this general scheme could actually work with an iterator instead...
        self.tokens.append(None) # Sentinel meaning EOF; assumed disjoint from all Symbol texts.
        self.i = 0
        self.calls = []
        self.stack = [[]]   # An explicit stack just for more debuggability

    def Empty(self, t):
        pass
    def Fail(self, t):
        raise SyntaxError("Unexpected token %r; expecting one of %r"
                          % (self.tokens[self.i], sorted(t.possibles)))
    def Symbol(self, t):
        if self.tokens[self.i] == t.text:
            self.i += 1
        else:
            raise SyntaxError("Missing %r" % t)
    def Call(self, t):
        self.calls.append(t.name)
        self.stack.append([])
#        print zip(self.calls, self.stack), 'call', t.name
        self(self.rules[t.name])
        result = self.stack.pop()
        self.stack[-1].extend(result)
        self.calls.pop()
#        print zip(self.calls, self.stack), 'returned', t.name
    def Branch(self, t):
        tok = self.tokens[self.i]
        for kinds, alt in t.cases:
            if tok in [s.text for s in kinds]: # XXX awkward
                return self(alt)
        self(t.default)
    def Chain(self, t):
        self(t.e1)
        self(t.e2)
    def Loop(self, t):
        foo = zet(token.text for token in t.firsts) # XXX same awkwardness
        while self.tokens[self.i] in foo:
            self(t.body)
    def Action(self, t):
        if self.actions:
            action = self.actions[t.name]
            frame = self.stack[-1]
            before = frame[:]
#            print self.stack, t.name, '...'
            frame[:] = [action(*frame)]
#            print '  ', t.name, '-->', self.stack


# Smoke test

bad = r"""
A: A.
B: 'b'.
B: A.
Z: Z | Z 'z'.
"""

## badg = Grammar(bad, {})
## badg.errors
#. ["Duplicate definitions: ['B']", 'A: Left recursion', "Z: Branches overlap: [Symbol('z', 'literal')]", 'Z: Left recursion']

eg = r"""
A: B 'x' A | 'y'.
B: 'b'.
C: .

exp:    term ( '+' exp :add
             | '-' exp :sub
             | ).
term:   factor ('*' factor :mul)*.
factor: 'x' :X | '(' exp ')'.
"""

## import operator
## actions = dict(X=lambda: 3, **operator.__dict__)

## egg = Grammar(eg, actions)
## for r in egg.nonterminals: print '%-8s %s' % (r, egg.rules[r])
#. A        Either(Chain(Call('B'), Chain(Symbol('x', 'literal'), Call('A'))), Symbol('y', 'literal'))
#. B        Symbol('b', 'literal')
#. C        Empty()
#. exp      Chain(Call('term'), Either(Chain(Symbol('+', 'literal'), Chain(Call('exp'), Action('add'))), Either(Chain(Symbol('-', 'literal'), Chain(Call('exp'), Action('sub'))), Empty())))
#. term     Chain(Call('factor'), Star(Chain(Symbol('*', 'literal'), Chain(Call('factor'), Action('mul')))))
#. factor   Either(Chain(Symbol('x', 'literal'), Action('X')), Chain(Symbol('(', 'literal'), Chain(Call('exp'), Symbol(')', 'literal'))))

## egg.show_analysis()
#. A        False  b y
#. B        False  b
#. C        True   
#. exp      False  ( x
#. term     False  ( x
#. factor   False  ( x

## for r in egg.nonterminals: print '%-8s %s' % (r, directify(egg.rules[r], egg.ana))
#. A        Branch([(frozenset([Symbol('b', 'literal')]), Chain(Call('B'), Chain(Symbol('x', 'literal'), Call('A')))), (frozenset([Symbol('y', 'literal')]), Symbol('y', 'literal'))], Fail(frozenset([Symbol('b', 'literal'), Symbol('y', 'literal')])))
#. B        Symbol('b', 'literal')
#. C        Empty()
#. exp      Chain(Call('term'), Branch([(frozenset([Symbol('+', 'literal')]), Chain(Symbol('+', 'literal'), Chain(Call('exp'), Action('add')))), (frozenset([Symbol('-', 'literal')]), Chain(Symbol('-', 'literal'), Chain(Call('exp'), Action('sub'))))], Empty()))
#. term     Chain(Call('factor'), Loop(frozenset([Symbol('*', 'literal')]), Chain(Symbol('*', 'literal'), Chain(Call('factor'), Action('mul')))))
#. factor   Branch([(frozenset([Symbol('x', 'literal')]), Chain(Symbol('x', 'literal'), Action('X'))), (frozenset([Symbol('(', 'literal')]), Chain(Symbol('(', 'literal'), Chain(Call('exp'), Symbol(')', 'literal'))))], Fail(frozenset([Symbol('x', 'literal'), Symbol('(', 'literal')])))

## egg.parse("".split(), start='B')
#. Missing Symbol('b', 'literal') at 0
## egg.parse("b b".split(), start='B')
#. ok at 1 []
## egg.parse("b b".split(), start='A')
#. Missing Symbol('x', 'literal') at 1
## egg.parse("b x".split(), start='A')
#. Unexpected token None; expecting one of [Symbol('b', 'literal'), Symbol('y', 'literal')] at 2
## egg.parse("b x y".split(), start='A')
#. ok at 3 []
## egg.parse("b x b x y".split(), start='A')
#. ok at 5 []

## egg.parse("x", start='exp')
#. ok at 1 [3]
## egg.parse("x+", start='exp')
#. Unexpected token None; expecting one of [Symbol('(', 'literal'), Symbol('x', 'literal')] at 2
## egg.parse("x+x", start='exp')
#. ok at 3 [6]
## egg.parse("x+x*x", start='exp')
#. ok at 5 [12]
## egg.parse("x+(x*x+x)", start='exp')
#. ok at 9 [15]
