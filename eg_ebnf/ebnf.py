"""
Parse a grammar, check that it's LL(1), and emit C code to parse according to it.
"""

import codecs
from collections import Counter
from structs import Struct, Visitor
import parson
import metagrammar
zet = frozenset

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

    def gen_kinds(self):
        return '\n'.join(gen_kinds(self))

    def gen_parser(self):
        return '\n'.join(codegen(self))

    def parse(self, tokens, start='start'):
        parsing = Parsing(self.directed, self.actions, tokens)
        parsing.calls.append(start)
        try:
            parsing(self.directed[start])
        except SyntaxError, e:
            print e, "at %d" % parsing.i
        else:
            print 'ok at', parsing.i, parsing.stack[0]

    def compile(self):
        labels = {}
        insns = []
        for name in self.nonterminals:
            labels[name] = len(insns)
            insns.extend(compiling(self.directed[name]))
            insns.append(('return', None))
        # TODO: make sure the client knows about self.errors
        return Code(insns, labels, self.actions)


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
    return fixpoint(rules, empty_set, lambda fst: First(nul, fst)) # TODO better naming

class First(Visitor):
    def __init__(self, nul, fst):
        self.nul = nul
        self.fst = fst

    def Empty(self, t):  return empty_set
    def Symbol(self, t): return zet([t])
    def Call(self, t):   return self.fst[t.name]
    def Either(self, t): return self(t.e1) | self(t.e2)
    def Chain(self, t):  return self(t.e1) | (self(t.e2) if self.nul(t.e1) else empty_set)
    def Star(self, t):   return self(t.e1)
    def Action(self, t): return empty_set

empty_set = zet()


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
        if not cases:       return Fail(empty_set)
        if len(cases) == 1: return cases[0][1]
        possibles = zet().union(*map(ana.firsts, ts))
        defaults = [Fail(possibles)]
    # We always just use the first default, because we only require
    # this to work for an LL(1) grammar.
    if not cases: return defaults[0]
    return Branch(cases, defaults[0])


# Generate a parser in C

# TODO shouldn't an EOF also be a kind?
def gen_kinds(grammar):
    tokens = grammar_symbols(grammar)
    kinds = sorted(map(c_encode_token, tokens))
    yield 'enum {'
    for kind in kinds:
        yield kind + ','
    yield '};'

def grammar_symbols(grammar):
    return empty_set.union(*map(collect_symbols, grammar.directed.values()))

class CollectSymbols(Visitor):
    def Symbol(self, t):  return zet([t])
    def Branch(self, t):  return self(t.default).union(*[zet(kinds) | self(alt)
                                                         for kinds,alt in t.cases])
    def Chain(self, t):   return self(t.e1) | self(t.e2)
    def Loop(self, t):    return zet(t.firsts) | self(t.body)
    def default(self, t): return empty_set
collect_symbols = CollectSymbols()

def gen_lexer_fns(grammar):
    syms = grammar_symbols(grammar)
    assert all(t.text for t in syms)
    assert len(syms) == len(zet(t.text for t in syms))
    lits = zet(t for t in syms if t.kind == 'literal')  # TODO these don't need to be sets
    kwds = zet(t for t in syms if t.kind == 'keyword')
    yield gen_lexer_fn('lex_lits', lits)
    yield ''
    yield gen_lexer_fn('lex_keywords', kwds)    
    # TODO skip lex_keywords if no keywords. In principle there might be no lits, too.

def gen_lexer_fn(name, syms):
    return ('void %s(void) %s'
            % (name, embrace('\n'.join(gen_trie_lexer(syms)))))

def gen_trie_lexer(syms):
    trie = sprout({t.text: t for t in syms})
    for line in gen_lex_dispatch(trie, 0):
        yield line
#    yield 'lex_error("XXX");'   # XXX return a status instead

def sprout(rel):
    """Given a map of {string: value}, represent it as a trie
    (opt_value_for_empty_string, {leading_char: subtrie})."""
    parts = map_from_relation((k[0], (k[1:], v))
                              for k,v in rel.items() if k)
    return (rel.get(''),
            {head: sprout(dict(tails)) for head,tails in parts.items()})

def map_from_relation(pairs):
    result = {}
    for k, v in pairs:
        result.setdefault(k, []).append(v)
    return result

def gen_lex_dispatch((opt_on_empty, branches), offset):
    heads = sorted(branches.keys())
    if opt_on_empty:
        default = ('token.kind = %s; scan += %d; return;'
                   % (c_encode_token(opt_on_empty), offset))
    else:
        default = ''
    if heads:
        yield 'switch (scan[%d]) {' % offset
        for head in heads:
            yield 'case %s:' % c_char_literal(head)
            for line in gen_lex_dispatch(branches[head], offset + 1):
                yield '  ' + line
            yield '  break;'
        if default:
            yield 'default:'
            yield '  ' + default
        yield '}'
    elif default:
        yield default

def c_char_literal(ch):
    # TODO anywhere this doesn't match C?
    return "'%s'" % codecs.encode(ch, 'string_escape')

def c_encode_token(token):
    # TODO rename to TOKEN_%s or something
    return 'kind_%s' % ''.join(escapes.get(c, c) for c in token.text)

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
    for plaint in grammar.errors:
        yield '// ' + plaint
    if grammar.errors: yield ''
    for block in gen_lexer_fns(grammar):
        yield block
    yield ''
    for name in grammar.nonterminals:
        yield 'void parse_%s(void);' % name
    for name in grammar.nonterminals:
        body = gen(grammar.directed[name])
        yield ''
        yield 'void parse_%s(void) %s' % (name, embrace(body))

def embrace(s): return '{%s\n}' % indent('\n' + s)
def indent(s): return s.replace('\n', '\n  ')

class Gen(Visitor):
    def Empty(self, t):  return ''
    def Symbol(self, t): return 'eat(%s);' % c_encode_token(t)
    def Call(self, t):   return 'parse_%s();' % t.name
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
            cases = [(','.join(sorted(s.text for s in kinds)), dest)
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
                if tokens[i] == arg.text:
                    i += 1
                else:
                    raise SyntaxError("Missing %r" % arg)
            elif op == 'branch':
                cases, default = arg
                for kinds, dest in cases:
                    if tokens[i] in [s.text for s in kinds]: # XXX awkward
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
    def Empty(self, t):  return []
    def Symbol(self, t): return [('eat', t)]
    def Call(self, t):   return [('call', t.name)]
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
#. Missing 'b' at 0
## egg.parse("b b".split(), start='B')
#. ok at 1 []
## egg.parse("b b".split(), start='A')
#. Missing 'x' at 1
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
#. ok at 3 [6]
## egg.parse("x+(x*x+x)", start='exp')
#. Missing ')' at 4

## egc = egg.compile()
## egc.show()
#. A            0 branch ([('b', 0), ('y', 4)], 6)
#.              1 call   'B'
#.              2 eat    Symbol('x', 'literal')
#.              3 call   'A'
#.              4 jump   3
#.              5 eat    Symbol('y', 'literal')
#.              6 jump   1
#.              7 fail   frozenset([Symbol('b', 'literal'), Symbol('y', 'literal')])
#.              8 return ''
#. B            9 eat    Symbol('b', 'literal')
#.             10 return ''
#. C           11 return ''
#. exp         12 call   'term'
#.             13 branch ([('+', 0), ('-', 4)], 8)
#.             14 eat    Symbol('+', 'literal')
#.             15 call   'exp'
#.             16 act    'add'
#.             17 jump   4
#.             18 eat    Symbol('-', 'literal')
#.             19 call   'exp'
#.             20 act    'sub'
#.             21 jump   0
#.             22 return ''
#. term        23 call   'factor'
#.             24 branch ([('*', 0)], 4)
#.             25 eat    Symbol('*', 'literal')
#.             26 call   'factor'
#.             27 act    'mul'
#.             28 jump   -5
#.             29 return ''
#. factor      30 branch ([('x', 0), ('(', 3)], 7)
#.             31 eat    Symbol('x', 'literal')
#.             32 act    'X'
#.             33 jump   5
#.             34 eat    Symbol('(', 'literal')
#.             35 call   'exp'
#.             36 eat    Symbol(')', 'literal')
#.             37 jump   1
#.             38 fail   frozenset([Symbol('x', 'literal'), Symbol('(', 'literal')])
#.             39 return ''
### egc.parse("x", start='exp')
### egc.parse("x+x-x", start='exp')
### egc.parse("x+(x*x+x)", start='exp')


## print egg.gen_parser()
#. void lex_lits(void) {
#.   switch (scan[0]) {
#.   case '(':
#.     token.kind = kind__LPAREN; scan += 1; return;
#.     break;
#.   case ')':
#.     token.kind = kind__RPAREN; scan += 1; return;
#.     break;
#.   case '*':
#.     token.kind = kind__STAR; scan += 1; return;
#.     break;
#.   case '+':
#.     token.kind = kind__PLUS; scan += 1; return;
#.     break;
#.   case '-':
#.     token.kind = kind__DASH; scan += 1; return;
#.     break;
#.   case 'b':
#.     token.kind = kind_b; scan += 1; return;
#.     break;
#.   case 'x':
#.     token.kind = kind_x; scan += 1; return;
#.     break;
#.   case 'y':
#.     token.kind = kind_y; scan += 1; return;
#.     break;
#.   }
#. }
#. 
#. void lex_keywords(void) {
#.   
#. }
#. 
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
