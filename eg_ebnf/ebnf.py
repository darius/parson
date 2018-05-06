"""
Parse a grammar, check that it's LL(1), and emit C code to parse according to it.
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
        self.inter = {name: intermediate(rule, self.ana)
                      for name, rule in self.rules.items()}

    def show_analysis(self):
        for r in self.nonterminals:
            nul = self.ana.nullable(self.rules[r])
            fst = self.ana.firsts(self.rules[r])
            print '%-8s %-6s %s' % (r, nul, ' '.join(sorted(fst)))

    def gen_kinds(self):
        return '\n'.join(gen_kinds(self))

    def gen_parser(self):
        return '\n'.join(codegen(self))

    def print_parser(self):
        for plaint in self.errors:
            print '//', plaint
        if self.errors: print
        print self.gen_parser()
    
    def parse(self, tokens, start='start'):
        parsing = Parsing(self.inter, self.actions, tokens)
        parsing.calls.append(start)
        try:
            parsing(self.inter[start])
        except SyntaxError, e:
            print e, "at %d" % parsing.i
        else:
            print 'ok at', parsing.i, parsing.stack[0]

    def compile(self):
        labels = {}
        insns = []
        for name in self.nonterminals:
            labels[name] = len(insns)
            insns.extend(compiling(self.inter[name]))
            insns.append(('return', None))
        # TODO: make sure the client knows about self.errors
        return Code(insns, labels, self.actions)


# Check that the grammar is well-formed and LL(1)
# TODO: what about left recursion

def check(grammar):
    dups = find_duplicates(grammar.nonterminals)
    if dups:
        grammar.errors.append("Duplicate definitions: %r" % dups)
    def error(plaint):
        grammar.errors.append('%s: %s' % (name, plaint))
    for name in grammar.nonterminals:
        Checker(grammar.ana, error)(grammar.rules[name])

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


# Intermediate form    TODO better name
# Embed the result of the LL(1) analysis where it'll be needed by
# an interpreter or compiler of the grammar.

# firsts is the first-set of body.
class Loop(Struct('firsts body')): pass

# Each case is a pair (kinds, t) where kinds is the first-set of
# t. Every Branch has a catch-all, 'default'. It's a Fail unless the
# source grammar supplies a nullable case. (This catch-all could be
# avoided if we could know that the cases are exhaustive.)
class Branch(Struct('cases default')): pass

# possibles is a frozenset of the tokens that would have made the
# parse not fail at this point.
class Fail(Struct('possibles')): pass

class Intermediate(Visitor):
    def Either(self, t, ana):  return gen_branch(flatten(t), ana)
    def Chain(self, t, ana):   return metagrammar.Chain(self(t.e1, ana),
                                                        self(t.e2, ana))
    def Star(self, t, ana):    return Loop(ana.firsts(t.e1), self(t.e1, ana))
    def default(self, t, ana): return t
intermediate = Intermediate()

class Flatten(Visitor):
    def Either(self, t):  return self(t.e1) + self(t.e2)
    def default(self, t): return [t]
flatten = Flatten()

def gen_branch(ts, ana):
    cases = []
    defaults = []
    for t in ts:
        im = intermediate(t, ana)
        if ana.nullable(t):
            defaults.append(im)
        else:
            firsts = ana.firsts(t)
            if firsts: cases.append((firsts, im))

    if not defaults:
        if not cases:       return Fail(empty_set)
        if len(cases) == 1: return cases[0][1]
        possibles = frozenset().union(*map(ana.firsts, ts))
        defaults = [Fail(possibles)]
    # We always just use the first default, because we only require
    # this to work for an LL(1) grammar.
    if not cases: return defaults[0]
    return Branch(cases, defaults[0])


# Generate a parser in pseudo-C

def gen_kinds(grammar):
    kinds = set().union(*map(collect_kinds, grammar.inter.values()))
    yield 'enum {'
    for kind in kinds:
        yield kind + ','
    yield '};'

class CollectKinds(Visitor):
    def Symbol(self, t):  return set([c_encode_token(t.text)])
    def Branch(self, t):  return set().union(*[set(map(c_encode_token, kinds)) | self(alt)
                                               for kinds,alt in t.cases])
    def Chain(self, t):   return self(t.e1) | self(t.e2)
    def Loop(self, t):    return set(map(c_encode_token, t.firsts)) | self(t.body)
    def default(self, t): return set()
collect_kinds = CollectKinds()

def c_encode_token(token):
    return 'kind_%s' % ''.join(escapes.get(c, c) for c in token)

escapes = {
    '!': '_BANG',
    '@': '_AT',
    '#': '_HASH',
    '$': '_DOLLAR',
    '%': '_PERCENT',
    '^': '_HAT',
    '&': '_AMPERSAND',
    '*': '_STAR',
    '(': '_LPAREN',
    ')': '_RPAREN',
    '-': '_DASH',
    '_': '_UNDERSCORE',
    '\\': '_BACKSLASH',
    '|': '_BAR',
    "'": '_QUOTE',
    '"': '_DOUBLEQUOTE',
    '/': '_SLASH',
    '?': '_QUESTION',
    ',': '_COMMA',
    '.': '_DOT',
    '<': '_LESS',
    '>': '_GREATER',
    '[': '_LBRACKET',
    ']': '_RBRACKET',
    '=': '_EQUALS',
    '+': '_PLUS',
    '`': '_BACKQUOTE',
    '~': '_TILDE',
    '{': '_LBRACE',
    '}': '_RBRACE',
    ';': '_SEMICOLON',
    ':': '_COLON',
}

def codegen(grammar):
    for name in grammar.nonterminals:
        yield 'void parse_%s(void);' % name
    for name in grammar.nonterminals:
        body = gen(grammar.inter[name])
        yield ''
        yield 'void parse_%s(void) %s' % (name, embrace(body))

def embrace(s): return '{%s\n}' % indent('\n' + s)
def indent(s): return s.replace('\n', '\n  ')

class Gen(Visitor):
    def Call(self, t):   return 'parse_%s();' % t.name
    def Empty(self, t):  return ''
    def Symbol(self, t): return 'eat(%s);' % c_encode_token(t.text)
    def Branch(self, t): return gen_switch(t)
    def Fail(self, t):   return 'parser_fail();'
    def Chain(self, t):  return '\n'.join(filter(None, [self(t.e1), self(t.e2)]))
    def Loop(self, t):   return gen_while(t.firsts, self(t.body))
    def Action(self, t): return ''
gen = Gen()

def gen_while(firsts, body):
    test = ' || '.join(map(gen_test, sorted(firsts)))
    return 'while (%s) %s' % (test, embrace(body))

def gen_test(token):
    return 'token.kind == %s' % c_encode_token(token)

def gen_switch(t):
    cases = ['%s %s' % ('\n'.join('case %s:' % c_encode_token(c)
                                  for c in sorted(kinds)),
                        embrace(gen(alt)))
             for kinds, alt in t.cases]
    default = 'default: ' + embrace(gen(t.default))
    return 'switch (token.kind) ' + embrace(' break;\n'.join(cases + [default]))


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
    def Fail(self, t):
        raise SyntaxError("Unexpected token %r; expecting one of %r"
                          % (self.tokens[self.i], sorted(t.possibles)))
    def Symbol(self, t):
        if self.tokens[self.i] == t.text:
            self.i += 1
        else:
            raise SyntaxError("Missing %r" % t.text)
    def Branch(self, t):
        tok = self.tokens[self.i]
        for kinds, alt in t.cases:
            if tok in kinds:
                return self(alt)
        self(t.default)
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
            cases, default = arg
            cases = [(','.join(sorted(kinds)), dest)
                     for kinds, dest in cases]
            arg = cases, default
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
                cases, default = arg
                for kinds, dest in cases:
                    if tokens[i] in kinds:
                        pc += dest
                        break
                else:
                    pc += default
            elif op == 'jump':
                pc += arg
            elif op == 'act':
                action = self.actions[arg]
                frame = frames[-1]
                frame[:] = [action(*frame)]
            elif op == 'fail':
                raise SyntaxError("Unexpected token %r; expecting one of %r"
                                  % (tokens[i], sorted(arg)))
            else:
                assert False

class Compiling(Visitor):
    def Call(self, t):   return [('call', t.name)]
    def Empty(self, t):  return []
    def Symbol(self, t): return [('eat', t.text)]
    def Branch(self, t): return compile_branch(t)
    def Fail(self, t):   return [('fail', t.possibles)]
    def Chain(self, t):  return self(t.e1) + self(t.e2)
    def Loop(self, t):   return compile_loop(t)
    def Action(self, t): return [('act', t.name)]
compiling = Compiling()

def compile_branch(t):
    cases = []
    insns = []
    fixups = []
    for kinds, alt in t.cases:
        dest = len(insns)       # Offset from the branch insn
        cases.append((kinds, dest))
        insns.extend(compiling(alt))
        fixups.append(len(insns))
        insns.append(None)      # to be fixed up
    default = len(insns)        # Offset from the branch insn
    insns.extend(compiling(t.default))
    for addr in fixups:
        insns[addr] = ('jump', len(insns) - (addr + 1)) # Skip to the common exit point
    insns.insert(0, ('branch', (cases, default)))
    return insns

def compile_loop(t):
    body = compiling(t.body)
    return ([('branch', ([(t.firsts, 0)], len(body)+1))]
            + body
            + [('jump', -len(body)-2)])


# Smoke test

bad = r"""
A: A.
B: 'b'.
B: A.
"""

## badg = Grammar(bad, {})
## badg.errors
#. ["Duplicate definitions: ['B']"]

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

## for r in egg.nonterminals: print '%-8s %s' % (r, intermediate(egg.rules[r], egg.ana))
#. A        Branch([(frozenset(['b']), Chain(Call('B'), Chain(Symbol('x'), Call('A')))), (frozenset(['y']), Symbol('y'))], Fail(frozenset(['y', 'b'])))
#. B        Symbol('b')
#. C        Empty()
#. exp      Chain(Call('term'), Branch([(frozenset(['+']), Chain(Symbol('+'), Chain(Call('exp'), Action('add')))), (frozenset(['-']), Chain(Symbol('-'), Chain(Call('exp'), Action('sub'))))], Empty()))
#. term     Chain(Call('factor'), Loop(frozenset(['*']), Chain(Symbol('*'), Chain(Call('factor'), Action('mul')))))
#. factor   Branch([(frozenset(['x']), Chain(Symbol('x'), Action('X'))), (frozenset(['(']), Chain(Symbol('('), Chain(Call('exp'), Symbol(')'))))], Fail(frozenset(['x', '('])))

## egg.parse("".split(), start='B')
#. Missing 'b' at 0
## egg.parse("b b".split(), start='B')
#. ok at 1 []
## egg.parse("b b".split(), start='A')
#. Missing 'x' at 1
## egg.parse("b x".split(), start='A')
#. Unexpected token None; expecting one of ['b', 'y'] at 2
## egg.parse("b x y".split(), start='A')
#. ok at 3 []
## egg.parse("b x b x y".split(), start='A')
#. ok at 5 []

## egg.parse("x", start='exp')
#. ok at 1 [3]
## egg.parse("x+", start='exp')
#. Unexpected token None; expecting one of ['(', 'x'] at 2
## egg.parse("x+x", start='exp')
#. ok at 3 [6]
## egg.parse("x+x*x", start='exp')
#. ok at 5 [12]
## egg.parse("x+(x*x+x)", start='exp')
#. ok at 9 [15]

## egc = egg.compile()
## egc.show()
#. A            0 branch ([('b', 0), ('y', 4)], 6)
#.              1 call   'B'
#.              2 eat    'x'
#.              3 call   'A'
#.              4 jump   3
#.              5 eat    'y'
#.              6 jump   1
#.              7 fail   frozenset(['y', 'b'])
#.              8 return ''
#. B            9 eat    'b'
#.             10 return ''
#. C           11 return ''
#. exp         12 call   'term'
#.             13 branch ([('+', 0), ('-', 4)], 8)
#.             14 eat    '+'
#.             15 call   'exp'
#.             16 act    'add'
#.             17 jump   4
#.             18 eat    '-'
#.             19 call   'exp'
#.             20 act    'sub'
#.             21 jump   0
#.             22 return ''
#. term        23 call   'factor'
#.             24 branch ([('*', 0)], 4)
#.             25 eat    '*'
#.             26 call   'factor'
#.             27 act    'mul'
#.             28 jump   -5
#.             29 return ''
#. factor      30 branch ([('x', 0), ('(', 3)], 7)
#.             31 eat    'x'
#.             32 act    'X'
#.             33 jump   5
#.             34 eat    '('
#.             35 call   'exp'
#.             36 eat    ')'
#.             37 jump   1
#.             38 fail   frozenset(['x', '('])
#.             39 return ''
### egc.parse("x", start='exp')
### egc.parse("x+x-x", start='exp')
### egc.parse("x+(x*x+x)", start='exp')


## egg.print_parser()
#. void parse_A(void);
#. void parse_B(void);
#. void parse_C(void);
#. void parse_exp(void);
#. void parse_term(void);
#. void parse_factor(void);
#. 
#. void parse_A(void) {
#.   switch (token.kind) {
#.     case kind_b: {
#.       parse_B();
#.       eat(kind_x);
#.       parse_A();
#.     } break;
#.     case kind_y: {
#.       eat(kind_y);
#.     } break;
#.     default: {
#.       parser_fail();
#.     }
#.   }
#. }
#. 
#. void parse_B(void) {
#.   eat(kind_b);
#. }
#. 
#. void parse_C(void) {
#.   
#. }
#. 
#. void parse_exp(void) {
#.   parse_term();
#.   switch (token.kind) {
#.     case kind__PLUS: {
#.       eat(kind__PLUS);
#.       parse_exp();
#.     } break;
#.     case kind__DASH: {
#.       eat(kind__DASH);
#.       parse_exp();
#.     } break;
#.     default: {
#.       
#.     }
#.   }
#. }
#. 
#. void parse_term(void) {
#.   parse_factor();
#.   while (token.kind == kind__STAR) {
#.     eat(kind__STAR);
#.     parse_factor();
#.   }
#. }
#. 
#. void parse_factor(void) {
#.   switch (token.kind) {
#.     case kind_x: {
#.       eat(kind_x);
#.     } break;
#.     case kind__LPAREN: {
#.       eat(kind__LPAREN);
#.       parse_exp();
#.       eat(kind__RPAREN);
#.     } break;
#.     default: {
#.       parser_fail();
#.     }
#.   }
#. }
