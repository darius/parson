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

class Grammar(object):
    def __init__(self, text, actions=None):
        self.actions = actions
        pairs = metaparser(text)
        self.nonterminals = tuple(pair[0] for pair in pairs)
        self.rules = dict(pairs)
        self.ana = analyze(self)
        self.errors = []
        check(self)

    def show_analysis(self):
        for r in self.nonterminals:
            nul = self.ana.nullable(self.rules[r])
            fst = self.ana.firsts(self.rules[r])
            print '%-8s %-6s %s' % (r, nul, ' '.join(sorted(fst)))

    def gen_parser(self):
        return '\n'.join(codegen(self))

    def print_parser(self):
        for plaint in self.errors:
            print '//', plaint
        if self.errors: print
        print self.gen_parser()
    
    def parse(self, tokens, start='start'):
        rules = {name: intermediate(self.rules[name], self.ana)
                 for name in self.nonterminals}
        parsing = Parsing(rules, self.actions, tokens)
        parsing.calls.append(start)
        try:
            parsing(rules[start])
        except SyntaxError, e:
            print e, "at %d" % parsing.i
        else:
            print 'ok at', parsing.i, parsing.stack[0]

    def compile(self):
        labels = {}
        insns = []
        for name in self.nonterminals:
            labels[name] = len(insns)
            insns.extend(compiling(intermediate(self.rules[name], self.ana)))
            insns.append(('return', None))
        # TODO: make sure the client knows about self.errors
        return Code(insns, labels, self.actions)


# Check that the grammar is well-formed and LL(1)

def check(grammar):
    errors = []
    dups = find_duplicates(grammar.nonterminals)
    if dups:
        errors.append("Duplicate definitions: %r", dups)
    def error(plaint):
        errors.append('%s: %s' % (name, plaint))
    for name in grammar.nonterminals:
        Checker(grammar.ana, error)(grammar.rules[name])
    return errors

def find_duplicates(xs):
    counts = Counter(xs)
    return sorted(x for x,n in counts.items() if 1 < n)

class Checker(Visitor):
    def __init__(self, ana, error):
        self.ana = ana
        self.error = error

    def Either(self, t):
        ts = flatten(t)
        if 1 < len(ts):
            if 1 < sum(map(self.ana.nullable, ts)):
                self.error("Multiple defaults")
            first_sets = map(self.ana.firsts, ts)
            overlap = find_duplicates(token for fs in first_sets for token in fs)
            if overlap:
                self.error("Branches overlap: %r" % overlap)
        for leaf in ts:
            self(leaf)

    def Chain(self, t):
        self(t.e1)
        self(t.e2)

    def Star(self, t):
        if self.ana.nullable(t.e1):
            self.error("Unproductive loop")
        self(t.e1)

    def default(self, t):
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

    def Call(self, t):   return self.nul[t.name]
    def Empty(self, t):  return True
    def Symbol(self, t): return False
    def Either(self, t): return self(t.e1) | self(t.e2)
    def Chain(self, t):  return self(t.e1) & self(t.e2)
    def Star(self, t):   return True
    def Action(self, t): return True

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
    def Action(self, t): return empty_set

empty_set = frozenset()


# Intermediate form
# Embed the result of the LL(1) analysis where it's needed by
# an interpreter or compiler of the grammar.

class Branch(Struct('cases opt_default')): pass
class Loop(Struct('firsts body')): pass

class Intermediate(Visitor):
    def Call(self, t, ana):   return t
    def Empty(self, t, ana):  return t
    def Symbol(self, t, ana): return t
    def Either(self, t, ana): return gen_branch(flatten(t), ana)
    def Chain(self, t, ana):  return metagrammar.Chain(self(t.e1, ana),
                                                       self(t.e2, ana))
    def Star(self, t, ana):   return Loop(ana.firsts(t.e1), self(t.e1, ana))
    def Action(self, t, ana): return t
intermediate = Intermediate()

class Flatten(Visitor):
    def Either(self, t):  return self(t.e1) + self(t.e2)
    def default(self, t): return [t]
flatten = Flatten()

def gen_branch(ts, ana):
    cases = []
    opt_default = None
    for t in ts:
        im = intermediate(t, ana)
        if ana.nullable(t):
            opt_default = im
        else:
            firsts = ana.firsts(t)
            if firsts: cases.append((firsts, im))
    n = len(cases) + (1 if opt_default else 0)
    if n == 0:
        return metagrammar.Empty()
    elif n == 1:
        return opt_default or cases[0][1]
    else:
        return Branch(cases, opt_default)


# Generate a parser in pseudo-C

def codegen(grammar):
    for name in grammar.nonterminals:
        yield 'void %s(void);' % name
    for name in grammar.nonterminals:
        body = gen(intermediate(grammar.rules[name], grammar.ana))
        yield ''
        yield 'void %s(void) %s' % (name, embrace(body))

def embrace(s): return '{%s\n}' % indent('\n' + s)
def indent(s): return s.replace('\n', '\n  ')

class Gen(Visitor):
    def Call(self, t):   return '%s();' % t.name
    def Empty(self, t):  return ''
    def Symbol(self, t): return 'eat(%r);' % t.text
    def Branch(self, t): return gen_switch(t)
    def Chain(self, t):  return self(t.e1) + '\n' + self(t.e2) # TODO drop empty lines
    def Loop(self, t):   return gen_while(t.firsts, self(t.body))
    def Action(self, t): return ''
gen = Gen()

def gen_while(firsts, body):
    test = ' || '.join(map(gen_test, sorted(firsts)))
    return 'while (%s) %s' % (test, embrace(body))

def gen_test(token):
    return 'token == %r' % token

def gen_switch(t):
    branches = map(gen_case, t.cases)
    branches.append('default: %s' % (embrace(gen(t.opt_default)) if t.opt_default
                                     else '\n  abort();'))
    return 'switch (token) %s' % embrace('\n'.join(branches))

def gen_case((firsts, t)):
    labels = '\n'.join('case %r:' % c for c in sorted(firsts))
    return '%s %s break;' % (labels, embrace(gen(t)))


# Parse by interpretation
# (TODO maybe drop this in favor of the VM below)

class SyntaxError(Exception): pass

class Parsing(Visitor):
    def __init__(self, rules, actions, tokens):
        self.rules = rules
        self.actions = actions
        self.tokens = list(tokens) # Although this general scheme could actually work with an iterator instead...
        self.tokens.append(None) # Sentinel meaning EOF; assumed disjoint from all Symbol texts.
        self.i = 0
        self.calls = []
        self.stack = [[]]

    def Call(self, t):
        self.calls.append(t.name)
        self.stack.append([])
#        print zip(self.calls, self.stack), 'call', t.name
        self(self.rules[t.name])
        result = self.stack.pop()
        self.stack[-1].extend(result)
        self.calls.pop()
#        print zip(self.calls, self.stack), 'returned', t.name
    def Empty(self, t):
        pass
    def Symbol(self, t):
        if self.tokens[self.i] == t.text:
            self.i += 1
        else:
            raise SyntaxError("Missing %r" % t.text)
    def Branch(self, t):
        tok = self.tokens[self.i]
        for firsts, alt in t.cases:
            if tok in firsts:
                return self(alt)
        if t.opt_default:
            return self(t.opt_default)
        raise SyntaxError("Unexpected token %r" % tok)
    def Chain(self, t):
        self(t.e1)
        self(t.e2)
    def Loop(self, t):
        while self.tokens[self.i] in t.firsts:
            self(t.body)
    def Action(self, t):
        if self.actions:
            action = self.actions[t.name]
            frame = self.stack[-1]
            before = frame[:]
#            print self.stack, t.name, '...'
            frame[:] = [action(*frame)]
#            print '  ', t.name, '-->', self.stack


# Parse by interpreting a compiled VM

class Code(object):
    def __init__(self, insns, labels, actions):
        self.insns = insns
        self.labels = labels
        self.actions = actions
        self.label_of_addr = dict(zip(labels.values(), labels.keys()))

    def show(self):
        for pc in range(len(self.insns)):
            self.show_insn(pc)

    def show_insn(self, pc):
        label = self.label_of_addr.get(pc, '')
        op, arg = self.insns[pc]
        if op == 'return':
            arg = ''
        elif op == 'branch':
            x, y = arg
            y = [(','.join(sorted(kinds)), dest)
                 for kinds,dest in sorted(y, key=lambda (kinds,dest): dest)]
            arg = x, y
        print '%-10s %3d %-6s %r' % (label, pc, op, arg)

    def parse(self, tokens, start='start'):
        limit = 100
        tokens = list(tokens) + [None]  # EOF sentinel
        i = 0
        frames = [[]]
        return_stack = [None]
        pc = self.labels[start]
        print 'starting', pc
        while pc is not None:
            limit -= 1
            if limit <= 0: break
            print ' '*50, zip(return_stack, frames)
            self.show_insn(pc)
            op, arg = self.insns[pc]
            pc += 1
            if op == 'call':
                frames.append([])
                return_stack.append(pc)
                pc = self.labels[arg]
            elif op == 'return':
                pc = return_stack.pop()
                results = frames.pop()
                if pc is None:
                    return results
                frames[-1].extend(results)
            elif op == 'eat':
                if tokens[i] == arg:
                    i += 1
                else:
                    raise SyntaxError("Missing %r" % arg)
            elif op == 'branch':
                opt_default, cases = arg
                for kinds, dest in cases:
                    if tokens[i] in kinds:
                        pc += dest
                        break
                else:
                    if opt_default is not None:
                        pc += opt_default
                    else:
                        raise SyntaxError("Expecting one of %r"
                                          % (sum([kinds for kinds,dest in cases], ()),))
            elif op == 'jump':
                pc += arg
            elif op == 'act':
                action = self.actions[arg]
                frame = frames[-1]
                frame[:] = [action(*frame)]
            else:
                assert False

class Compiling(Visitor):
    def Call(self, t):   return [('call', t.name)]
    def Empty(self, t):  return []
    def Symbol(self, t): return [('eat', t.text)]
    def Branch(self, t): return compile_branch(t)
    def Chain(self, t):  return self(t.e1) + self(t.e2)
    def Loop(self, t):   return compile_loop(t)
    def Action(self, t): return [('act', t.name)]
compiling = Compiling()

def compile_branch(t):
    cases = []
    insns = []
    fixups = []
    for firsts, alt in t.cases:
        off = len(insns)        # Offset from the branch insn
        cases.append((firsts, off))
        insns.extend(compiling(alt))
        fixups.append(len(insns))
        insns.append(None)      # to be fixed up
    opt_default = None
    if t.opt_default:
        opt_default = len(insns) # Offset from the branch insn
        insns.extend(compiling(t.opt_default))
    for addr in fixups:
        insns[addr] = ('jump', len(insns) - (addr + 1)) # Skip to the common exit point
    insns.insert(0, ('branch', (opt_default, cases)))
    return insns

def compile_loop(t):
    body = compiling(t.body)
    return ([('branch', (len(body)+1, [(t.firsts, 0)]))]
            + body
            + [('jump', -len(body)-2)])


# Smoke test

## import operator
## actions = dict(X=lambda: 3, **operator.__dict__)

eg = """
A: B 'x' A | 'y'.
B: 'b'.
C: .

exp:    term ( '+' exp :add
             | '-' exp :sub
             | ).
term:   factor ('*' factor :mul)*.
factor: 'x' :X | '(' exp ')'.
"""

## egg = Grammar(eg, actions)
## for r in egg.nonterminals: print '%-8s %s' % (r, egg.rules[r])
#. A        Either(Chain(Call('B'), Chain(Symbol('x'), Call('A'))), Symbol('y'))
#. B        Symbol('b')
#. C        Empty()
#. exp      Chain(Call('term'), Either(Chain(Symbol('+'), Chain(Call('exp'), Action('add'))), Either(Chain(Symbol('-'), Chain(Call('exp'), Action('sub'))), Empty())))
#. term     Chain(Call('factor'), Star(Chain(Symbol('*'), Chain(Call('factor'), Action('mul')))))
#. factor   Either(Chain(Symbol('x'), Action('X')), Chain(Symbol('('), Chain(Call('exp'), Symbol(')'))))

## egg.show_analysis()
#. A        False  b y
#. B        False  b
#. C        True   
#. exp      False  ( x
#. term     False  ( x
#. factor   False  ( x

## egg.parse("".split(), start='B')
#. Missing 'b' at 0
## egg.parse("b b".split(), start='B')
#. ok at 1 []
## egg.parse("b b".split(), start='A')
#. Missing 'x' at 1
## egg.parse("b x".split(), start='A')
#. Unexpected token None at 2
## egg.parse("b x y".split(), start='A')
#. ok at 3 []
## egg.parse("b x b x y".split(), start='A')
#. ok at 5 []

## egg.parse("x", start='exp')
#. ok at 1 [3]
## egg.parse("x+", start='exp')
#. Unexpected token None at 2
## egg.parse("x+x", start='exp')
#. ok at 3 [6]
## egg.parse("x+x*x", start='exp')
#. ok at 5 [12]
## egg.parse("x+(x*x+x)", start='exp')
#. ok at 9 [15]

## egc = egg.compile()
## egc.show()
#. A            0 branch (None, [('b', 0), ('y', 4)])
#.              1 call   'B'
#.              2 eat    'x'
#.              3 call   'A'
#.              4 jump   2
#.              5 eat    'y'
#.              6 jump   0
#.              7 return ''
#. B            8 eat    'b'
#.              9 return ''
#. C           10 return ''
#. exp         11 call   'term'
#.             12 branch (8, [('+', 0), ('-', 4)])
#.             13 eat    '+'
#.             14 call   'exp'
#.             15 act    'add'
#.             16 jump   4
#.             17 eat    '-'
#.             18 call   'exp'
#.             19 act    'sub'
#.             20 jump   0
#.             21 return ''
#. term        22 call   'factor'
#.             23 branch (4, [('*', 0)])
#.             24 eat    '*'
#.             25 call   'factor'
#.             26 act    'mul'
#.             27 jump   -5
#.             28 return ''
#. factor      29 branch (None, [('x', 0), ('(', 3)])
#.             30 eat    'x'
#.             31 act    'X'
#.             32 jump   4
#.             33 eat    '('
#.             34 call   'exp'
#.             35 eat    ')'
#.             36 jump   0
#.             37 return ''
### egc.parse("x", start='exp')
### egc.parse("x+x-x", start='exp')
### egc.parse("x+(x*x+x)", start='exp')


## egg.print_parser()
#. void A(void);
#. void B(void);
#. void C(void);
#. void exp(void);
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
#.     case '+': {
#.       eat('+');
#.       exp();
#.       
#.     } break;
#.     case '-': {
#.       eat('-');
#.       exp();
#.       
#.     } break;
#.     default: {
#.       
#.     }
#.   }
#. }
#. 
#. void term(void) {
#.   factor();
#.   while (token == '*') {
#.     eat('*');
#.     factor();
#.     
#.   }
#. }
#. 
#. void factor(void) {
#.   switch (token) {
#.     case 'x': {
#.       eat('x');
#.       
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
