"""
Generate a parser in C.
"""

import codecs
from structs import Visitor

zet = frozenset
empty_zet = zet()

def gen_kinds_enum(self):
    return '\n'.join(gen_kinds(self))

def gen_parser(self):
    return '\n'.join(codegen(self))

# TODO shouldn't an EOF also be a kind?
def gen_kinds(grammar):
    tokens = grammar_symbols(grammar)
    kinds = sorted(map(c_encode_token, tokens))
    yield 'enum {'
    for kind in kinds:
        yield kind + ','
    yield '};'

def grammar_symbols(grammar):
    return empty_zet.union(*map(collect_symbols, grammar.directed.values()))

class CollectSymbols(Visitor):
    def Symbol(self, t):  return zet([t])
    def Branch(self, t):  return self(t.default).union(*[zet(kinds) | self(alt)
                                                         for kinds,alt in t.cases])
    def Chain(self, t):   return self(t.e1) | self(t.e2)
    def Loop(self, t):    return zet(t.firsts) | self(t.body)
    def default(self, t): return empty_zet
collect_symbols = CollectSymbols()

def gen_lexer_fns(grammar):
    syms = grammar_symbols(grammar)
    assert all(t.text for t in syms)
    assert len(syms) == len(zet(t.text for t in syms))
    lits = tuple(t for t in syms if t.kind == 'literal')
    kwds = tuple(t for t in syms if t.kind == 'keyword')
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


# Smoke test

## from ebnf import Grammar, eg
## import operator
## actions = dict(X=lambda: 3, **operator.__dict__)

## egg = Grammar(eg, actions)

## print gen_parser(egg)
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
