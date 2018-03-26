"""
Parse a grammar, check that it's LL(1), and emit C code to parse according to it.
TODO: stars/pluses etc.
TODO: design an action language along the lines of Parson or something
"""

from structs import Struct, Visitor
import parson
import grammar

parser = parson.Grammar(grammar.grammar_source).bind(grammar)

def parse(text):
    rules = dict(parser(text))  # TODO check for dupes
    return rules

Analysis = Struct('nullable firsts')

def expand(rules):
    ana = analyze(rules)
    for name in rules:
        print 'void %s(void);' % name
    print
    for name in rules:
        body = gen(rules[name], ana)
        print 'void %s(void) %s' % (name, embrace(body))
        print

def analyze(rules):
    rule_nullable = compute_nullables(rules)
    def my_nullable(t): return nullable(t, rule_nullable)
    def my_first(t, bounds): return first(t, bounds, my_nullable)
    rule_firsts = fixpoint(rules, empty_set, my_first) # XXX these names are too confusable
    def exact_first(t): return first(t, rule_firsts, my_nullable)
    return Analysis(my_nullable, exact_first)

def embrace(s): return '{%s\n}' % indent('\n' + s)
def indent(s): return s.replace('\n', '\n  ')

class Gen(Visitor):
    def Call(self, t, ana):
        return '%s();' % t.name
    def Empty(self, t, ana):
        return ''
    def Symbol(self, t, ana):
        return 'eat(%r);' % t.text
    def Either(self, t, ana):
        return gen_switch(flatten(t), ana)
    def Chain(self, t, ana):
        return self(t.e1, ana) + '\n' + self(t.e2, ana)
gen = Gen()

class Flatten(Visitor):
    def Either(self, t):  return self(t.e1) + self(t.e2)
    def default(self, t): return [t]
flatten = Flatten()

def gen_switch(ts, ana):
    if not ts:
        return ''
    if len(ts) == 1:
        return gen(ts[0], ana)
    first_sets = map(ana.firsts, ts)
    overlap = first_sets[0].intersection(*first_sets[1:])
    n_default = sum(map(ana.nullable, ts))
    warning = '// NOT LL(1)!\n' if overlap or 1 < n_default else ''
    return warning + ('switch (token) %s'
                      % embrace('\n'.join(branch(t, ana) for t in ts)))

def branch(t, ana):
    cases = ('default:' if ana.nullable(t)
             else '\n'.join('case %r:' % c for c in ana.firsts(t)))
    return '%s %s break;' % (cases, embrace(gen(t, ana)))

def fixpoint(rules, initial, f):
    bounds = {name: initial for name in rules}
    while True:
        prev_state = dict(bounds)
        for name in rules:
            bounds[name] = f(rules[name], bounds)
        if prev_state == bounds:
            return bounds

r"""
OK, what's LL(1)?
The first-sets of each either-branch must be disjoint.
Also, the argument of a Star must be non-nullable (not checked yet).

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

def compute_nullables(rules):
    return fixpoint(rules, True, nullable)

class Nullable(Visitor):
    def Call(self, t, bounds):   return bounds[t.name]
    def Empty(self, t, bounds):  return True
    def Symbol(self, t, bounds): return False
    def Either(self, t, bounds): return self(t.e1, bounds) | self(t.e2, bounds)
    def Chain(self, t, bounds):  return self(t.e1, bounds) & self(t.e2, bounds)
    def Star(self, t, bounds):   XXX
nullable = Nullable()

empty_set = frozenset()

class First(Visitor):
    def Call(self, t, bounds, nullable):   return bounds[t.name]
    def Empty(self, t, bounds, nullable):  return empty_set
    def Symbol(self, t, bounds, nullable): return frozenset([t.text])
    def Either(self, t, bounds, nullable): return self(t.e1, bounds, nullable) | self(t.e2, bounds, nullable)
    def Chain(self, t, bounds, nullable):  return (self(t.e1, bounds, nullable)
                                                   | (self(t.e2, bounds, nullable) if nullable(t.e1) else empty_set))
    def Star(self, t, bounds, nullable):   XXX
first = First()


# Smoke test

eg = """
A: B 'x' A | 'y'.
B: 'b'.
C: .

exp: term terms.
terms: addop exp | .
addop: ('+'|'-').
term: factor factors.
factors: '*' factors | .
factor: 'x' | '(' exp ')'.
"""

## for r,e in sorted(parser(eg)): print '%-8s %s' % (r, e)
#. A        Either(Chain(Call('B'), Chain(Symbol('x'), Call('A'))), Symbol('y'))
#. B        Symbol('b')
#. C        Empty()
#. addop    Either(Symbol('+'), Symbol('-'))
#. exp      Chain(Call('term'), Call('terms'))
#. factor   Either(Symbol('x'), Chain(Symbol('('), Chain(Call('exp'), Symbol(')'))))
#. factors  Either(Chain(Symbol('*'), Call('factors')), Empty())
#. term     Chain(Call('factor'), Call('factors'))
#. terms    Either(Chain(Call('addop'), Call('exp')), Empty())

## show_ana(parse(eg))
#. A        False  b y
#. B        False  b
#. C        True   
#. addop    False  + -
#. exp      False  ( x
#. factor   False  ( x
#. factors  True   *
#. term     False  ( x
#. terms    True   + -

def show_ana(rules):
    ana = analyze(rules)
    for r in sorted(rules):
        print '%-8s %-6s %s' % (r, ana.nullable(rules[r]), ' '.join(sorted(ana.firsts(rules[r]))))

## expand(parse(eg))
#. void A(void);
#. void addop(void);
#. void C(void);
#. void B(void);
#. void terms(void);
#. void factors(void);
#. void term(void);
#. void exp(void);
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
#.   }
#. }
#. 
#. void C(void) {
#.   
#. }
#. 
#. void B(void) {
#.   eat('b');
#. }
#. 
#. void terms(void) {
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
#. void factors(void) {
#.   switch (token) {
#.     case '*': {
#.       eat('*');
#.       factors();
#.     } break;
#.     default: {
#.       
#.     } break;
#.   }
#. }
#. 
#. void term(void) {
#.   factor();
#.   factors();
#. }
#. 
#. void exp(void) {
#.   term();
#.   terms();
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
#.   }
#. }
#. 
