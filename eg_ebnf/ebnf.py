"""
Parse a grammar, check that it's LL(1), and emit C code to parse according to it.
TODO: design an action language along the lines of Parson or something
TODO: generate an actually-useful parser
"""

from collections import Counter
from structs import Struct, Visitor
import parson
import metagrammar

metaparser = parson.Grammar(metagrammar.metagrammar_text).bind(metagrammar)

def metaparse(text):
    pairs = metaparser(text)
    nonterminals = tuple(pair[0] for pair in pairs)
    dups = find_duplicates(nonterminals)
    if dups:
        raise Exception("Duplicate definitions", dups)
    return Grammar(nonterminals, dict(pairs))

Grammar = Struct('nonterminals rules')

def find_duplicates(xs):
    counts = Counter(xs)
    return sorted(x for x,n in counts.items() if 1 < n)


# Generating a parser

def expand(grammar):
    ana = analyze(grammar)
    for name in grammar.nonterminals:
        print 'void %s(void);' % name
    for name in grammar.nonterminals:
        body = gen(grammar.rules[name], ana)
        print
        print 'void %s(void) %s' % (name, embrace(body))

def embrace(s): return '{%s\n}' % indent('\n' + s)
def indent(s): return s.replace('\n', '\n  ')

class Gen(Visitor):
    def Call(self, t, ana):   return '%s();' % t.name
    def Empty(self, t, ana):  return ''
    def Symbol(self, t, ana): return 'eat(%r);' % t.text
    def Either(self, t, ana): return gen_switch(flatten(t), ana)
    def Chain(self, t, ana):  return self(t.e1, ana) + '\n' + self(t.e2, ana) # TODO drop empty lines
    def Star(self, t, ana):   return gen_while(t.e1, ana)
gen = Gen()

class Flatten(Visitor):
    def Either(self, t):  return self(t.e1) + self(t.e2)
    def default(self, t): return [t]
flatten = Flatten()

def gen_while(t, ana):
    warning = ''
    if ana.nullable(t):
        warning += '// NOT LL(1)! Nullable star body'
    test = ' || '.join(map(gen_test, ana.firsts(t)))
    return warning + 'while (%s) %s' % (test, embrace(gen(t, ana)))

def gen_test(token):
    return 'token == %r' % token

def gen_switch(ts, ana):
    if not ts:
        return ''
    if len(ts) == 1:
        return gen(ts[0], ana)

    warning = ''

    n_default = sum(map(ana.nullable, ts))
    if 1 < n_default:
        warning += '// NOT LL(1)! Multiple defaults\n'

    first_sets = map(ana.firsts, ts)
    overlap = find_duplicates(token for fs in first_sets for token in fs)
    if overlap:
        warning += '// NOT LL(1)! Overlap: %r\n' % overlap

    branches = [branch(t, ana) for t in ts]
    if n_default == 0:
        branches.append('default:\n  abort();')
    return warning + 'switch (token) %s' % embrace('\n'.join(branches))

def branch(t, ana):
    cases = ('default:' if ana.nullable(t)
             else '\n'.join('case %r:' % c for c in sorted(ana.firsts(t))))
    return '%s %s break;' % (cases, embrace(gen(t, ana)))


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

    def Call(self, t):   return self.nul[t.name]
    def Empty(self, t):  return True
    def Symbol(self, t): return False
    def Either(self, t): return self(t.e1) | self(t.e2)
    def Chain(self, t):  return self(t.e1) & self(t.e2)
    def Star(self, t):   return True

def compute_firsts(rules, nul):
    return fixpoint(rules, empty_set, lambda fst: First(nul, fst)) # TODO better naming

class First(Visitor):
    def __init__(self, nul, fst):
        self.nul = nul
        self.fst = fst

    def Call(self, t):   return self.fst[t.name]
    def Empty(self, t):  return empty_set
    def Symbol(self, t): return frozenset([t.text])
    def Either(self, t): return self(t.e1) | self(t.e2)
    def Chain(self, t):  return self(t.e1) | (self(t.e2) if self.nul(t.e1) else empty_set)
    def Star(self, t):   return self(t.e1)

empty_set = frozenset()


# Smoke test

eg = """
A: B 'x' A | 'y'.
B: 'b'.
C: .

exp: term (addop exp | ).
addop: ('+'|'-').
term: factor ('*' factor)*.
factor: 'x' | '(' exp ')'.
"""

## egg = metaparse(eg)
## for r in egg.nonterminals: print '%-8s %s' % (r, egg.rules[r])
#. A        Either(Chain(Call('B'), Chain(Symbol('x'), Call('A'))), Symbol('y'))
#. B        Symbol('b')
#. C        Empty()
#. exp      Chain(Call('term'), Either(Chain(Call('addop'), Call('exp')), Empty()))
#. addop    Either(Symbol('+'), Symbol('-'))
#. term     Chain(Call('factor'), Star(Chain(Symbol('*'), Call('factor'))))
#. factor   Either(Symbol('x'), Chain(Symbol('('), Chain(Call('exp'), Symbol(')'))))

## show_ana(metaparse(eg))
#. A        False  b y
#. B        False  b
#. C        True   
#. exp      False  ( x
#. addop    False  + -
#. term     False  ( x
#. factor   False  ( x

def show_ana(grammar):
    ana = analyze(grammar)
    for r in grammar.nonterminals:
        print '%-8s %-6s %s' % (r, ana.nullable(grammar.rules[r]),
                                ' '.join(sorted(ana.firsts(grammar.rules[r]))))

## expand(metaparse(eg))
#. void A(void);
#. void B(void);
#. void C(void);
#. void exp(void);
#. void addop(void);
#. void term(void);
#. void factor(void);
#. 
#. void A(void) {
#.   switch (token) {
#.     case 'b': {
#.       B();
#.       eat('x');
#.       A();
#.     } break;
#.     case 'y': {
#.       eat('y');
#.     } break;
#.     default:
#.       abort();
#.   }
#. }
#. 
#. void B(void) {
#.   eat('b');
#. }
#. 
#. void C(void) {
#.   
#. }
#. 
#. void exp(void) {
#.   term();
#.   switch (token) {
#.     case '+':
#.     case '-': {
#.       addop();
#.       exp();
#.     } break;
#.     default: {
#.       
#.     } break;
#.   }
#. }
#. 
#. void addop(void) {
#.   switch (token) {
#.     case '+': {
#.       eat('+');
#.     } break;
#.     case '-': {
#.       eat('-');
#.     } break;
#.     default:
#.       abort();
#.   }
#. }
#. 
#. void term(void) {
#.   factor();
#.   while (token == '*') {
#.     eat('*');
#.     factor();
#.   }
#. }
#. 
#. void factor(void) {
#.   switch (token) {
#.     case 'x': {
#.       eat('x');
#.     } break;
#.     case '(': {
#.       eat('(');
#.       exp();
#.       eat(')');
#.     } break;
#.     default:
#.       abort();
#.   }
#. }
