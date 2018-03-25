"""
Parse a grammar, check that it's LL(1), and emit C code to parse according to it.
TODO: stars/pluses etc.
TODO: design an action language along the lines of Parson or something
"""

from structs import Struct, Visitor
from parson import Grammar

class Empty (Struct('')): pass
class Either(Struct('e1 e2')): pass
class Chain (Struct('e1 e2')): pass
class Symbol(Struct('text')): pass
class Call  (Struct('name')): pass

grammar_source = r"""
'' rule* :end.

rule         :  name ':' exp '.' :hug.

exp          :  term ('|' exp :Either)?
             |                :Empty.

term         :  factor (term :Chain)?.
factor       :  qstring  :Symbol
             |  name     :Call.

name         :  /([A-Za-z_]\w*)/.

qstring     ~:  /'/ quoted_char* /'/ FNORD :join.
quoted_char ~:  /\\(.)/ | /([^'])/.

FNORD       ~:  whitespace?.
whitespace  ~:  /(?:\s|#.*)+/.
"""
parser = Grammar(grammar_source)(Empty=Empty,
                                 Either=Either,
                                 Chain=Chain,
                                 Symbol=Symbol,
                                 Call=Call)

eg = """
A: B 'x' A | 'y'.
B: 'b'.
C: .

exp: term terms.
terms: '+' exp | '-' exp | .
term: factor factors.
factors: '*' factors | .
factor: 'x' | '(' exp ')'.
"""

## for rule in parser(eg): print rule
#. ('A', Either(Chain(Call('B'), Chain(Symbol('x'), Call('A'))), Symbol('y')))
#. ('B', Symbol('b'))
#. ('C', Empty())
#. ('exp', Chain(Call('term'), Call('terms')))
#. ('terms', Either(Chain(Symbol('+'), Call('exp')), Either(Chain(Symbol('-'), Call('exp')), Empty())))
#. ('term', Chain(Call('factor'), Call('factors')))
#. ('factors', Either(Chain(Symbol('*'), Call('factors')), Empty()))
#. ('factor', Either(Symbol('x'), Chain(Symbol('('), Chain(Call('exp'), Symbol(')')))))

def parse(text):
    rules = dict(parser(text))  # TODO check for dupes
    return rules

## parse(eg)
#. {'A': Either(Chain(Call('B'), Chain(Symbol('x'), Call('A'))), Symbol('y')), 'C': Empty(), 'B': Symbol('b'), 'terms': Either(Chain(Symbol('+'), Call('exp')), Either(Chain(Symbol('-'), Call('exp')), Empty())), 'factors': Either(Chain(Symbol('*'), Call('factors')), Empty()), 'term': Chain(Call('factor'), Call('factors')), 'exp': Chain(Call('term'), Call('terms')), 'factor': Either(Symbol('x'), Chain(Symbol('('), Chain(Call('exp'), Symbol(')'))))}
## compute_nullables(parse(eg))
#. {'A': False, 'C': True, 'B': False, 'terms': True, 'factors': True, 'term': False, 'exp': False, 'factor': False}
## compute_firsts(parse(eg))
#. {'A': frozenset(['y', 'b']), 'C': frozenset([]), 'B': frozenset(['b']), 'terms': frozenset(['+', '-']), 'factors': frozenset(['*']), 'term': frozenset(['x', '(']), 'exp': frozenset(['x', '(']), 'factor': frozenset(['x', '('])}

## expand(parse(eg))
#. void A(void);
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
#.       if (token != 'x') abort(); next();
#.       A();
#.     } break;
#.     case 'y': {
#.       if (token != 'y') abort(); next();
#.     } break;
#.   }
#. }
#. 
#. void C(void) {
#.   
#. }
#. 
#. void B(void) {
#.   if (token != 'b') abort(); next();
#. }
#. 
#. void terms(void) {
#.   switch (token) {
#.     case '+': {
#.       if (token != '+') abort(); next();
#.       exp();
#.     } break;
#.     case '-': {
#.       if (token != '-') abort(); next();
#.       exp();
#.     } break;
#.   }
#. }
#. 
#. void factors(void) {
#.   if (token != '*') abort(); next();
#.   factors();
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
#.       if (token != 'x') abort(); next();
#.     } break;
#.     case '(': {
#.       if (token != '(') abort(); next();
#.       exp();
#.       if (token != ')') abort(); next();
#.     } break;
#.   }
#. }
#. 

def expand(rules):
    rule_nullable = compute_nullables(rules)
    def my_nullable(t): return nullable(t, rule_nullable)
    def my_first(t, bounds): return first(t, bounds, my_nullable)
    rule_firsts = fixpoint(rules, empty_set, my_first) # XXX these names are too confusable
    def exact_first(t): return first(t, rule_firsts, my_nullable)
    for name in rules:
        print 'void %s(void);' % name
    print
    for name in rules:
        body = gen(rules[name], exact_first)
        print 'void %s(void) %s' % (name, embrace(body))
        print

def embrace(s): return '{%s\n}' % indent('\n' + s)
def indent(s): return s.replace('\n', '\n  ')

def compute_firsts(rules):      # (redundant temp def for testing)
    rule_nullable = compute_nullables(rules)
    def my_nullable(t): return nullable(t, rule_nullable)
    def my_first(t, bounds): return first(t, bounds, my_nullable)
    return fixpoint(rules, empty_set, my_first)

class Gen(Visitor):
    def Empty(self, t, firsts):
        return ''
    def Symbol(self, t, firsts):
        return 'if (token != %r) abort(); next();' % t.text
    def Call(self, t, firsts):
        return '%s();' % t.name
    def Either(self, t, firsts):
        return gen_either(flatten(t), firsts)
    def Chain(self, t, firsts):
        return self(t.e1, firsts) + '\n' + self(t.e2, firsts)

gen = Gen()

class Flatten(Visitor):
    def Either(self, t):  return self(t.e1) + self(t.e2)
    def Empty(self, t):   return []
    def default(self, t): return [t]
flatten = Flatten()

def gen_either(ts, firsts):
    assert ts, "No branches"
    if len(ts) == 1:
        return gen(ts[0], firsts)
    first_sets = map(firsts, ts)
    overlap = first_sets[0].intersection(*first_sets[1:])
    warning = '// NOT LL(1)!\n' if overlap else ''
    # TODO flatten nested switches
    return warning + ('switch (token) %s'
                      % embrace('\n'.join(branch(t, firsts) for t in ts)))

def branch(t, firsts):
    cases = '\n'.join('case %r:' % c for c in firsts(t))
    return '%s %s break;' % (cases, embrace(gen(t, firsts)))

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

firsts(Empty)            = {}                      # or make it {epsilon}?
firsts(Symbol(t))        = {t}
firsts(Call(r))          = firsts(rules[r])        # to closure
firsts(Either(e1, e2))   = firsts(e1) \/ firsts(e2)
firsts(Chain(e1, e2))    = firsts(e1) \/ (firsts(e2) if nullable(e1) else {})

nullable(Empty)          = Yes
nullable(Symbol(_))      = No
nullable(Call(r))        = nullable(rules[r])      # to closure
nullable(Either(e1, e2)) = nullable(e1) | nullable(e2)
nullable(Chain(e1, e2))  = nullable(e1) & nullable(e2)

Can we do this with one function instead of two? E.g. using {epsilon} as above?
In fact, couldn't EOF be a valid token to switch on? I don't think I'm accounting
for that ("follow sets", iirc).
"""

def compute_nullables(rules):
    return fixpoint(rules, True, nullable)

class Nullable(Visitor):
    def Empty(self, t, bounds):  return True
    def Symbol(self, t, bounds): return False
    def Call(self, t, bounds):   return bounds[t.name]
    def Either(self, t, bounds): return self(t.e1, bounds) | self(t.e2, bounds)
    def Chain(self, t, bounds):  return self(t.e1, bounds) & self(t.e2, bounds)
nullable = Nullable()

empty_set = frozenset()

class First(Visitor):
    def Empty(self, t, bounds, nullable):  return empty_set
    def Symbol(self, t, bounds, nullable): return frozenset([t.text])
    def Call(self, t, bounds, nullable):   return bounds[t.name]
    def Either(self, t, bounds, nullable): return self(t.e1, bounds, nullable) | self(t.e2, bounds, nullable)
    def Chain(self, t, bounds, nullable):  return (self(t.e1, bounds, nullable)
                                                   | (self(t.e2, bounds, nullable) if nullable(t.e1) else empty_set))

first = First()
