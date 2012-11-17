"""
Parsing with PEGs.
"""

import re

# Glossary:
#   peg     object representing a parsing expression
#   p, q    peg
#   s	    subject sequence. Usually a string, but only match() assumes that.
#   i       position in subject sequence
#   far     box holding the rightmost i reached so far
#           (except during negative matching with invert())
#   vals    values tuple
#   st      the state: an (i, vals) pair
#   fn      function (not a peg)

# A peg's run() function does the work. It takes (s, far, st) and
# returns a list of states, of length 0 or 1: i.e. either [] or
# [st]. (A more general kind of parser could return a list of any
# number of states, enumerated lazily; but that'd change our model
# both semantically (in (P|Q), Q can assume P didn't match) and in
# performance. We use a list anyway because it's convenient to code
# with list comprehensions.)

def Peg(x):
    """Make a peg from a Python value as appropriate for its type. For
    a string, that's a literal matcher; for a function it's a feed
    action (transform the current values tuple)."""
    if isinstance(x, _Peg):           return x
    if isinstance(x, (str, unicode)): return literal(x)
    if callable(x):                   return feed(x)
    raise ValueError("Not a Peg", x)

def recur(fn):
    "Return a peg p such that p = fn(p). This is like the Y combinator."
    p = delay(lambda: fn(p), 'recur(%s)', _fn_name(fn))
    return p

def delay(thunk, *face):        # XXX document face
    """Precondition: thunk() will return a peg p. We immediately
    return a peg q equivalent to that future p, but we'll call thunk()
    only once, and not until the first use of q. Use this for
    recursive grammars."""
    def run(s, far, st):
        q.run = Peg(thunk()).run
        return q.run(s, far, st)
    q = _Peg(face or ('delay(%s)', _fn_name(thunk)),
             run)
    return q

def _step(far, i):
    "Update far with the new position, i."
    far[0] = max(far[0], i)
    return i

def literal(string):
    "Return a peg that matches string exactly."
    return label(match(re.escape(string)),
                 'literal(%r)', string)

def match(regex):
    """Return a peg that matches what regex does, adding any captures
    to the values tuple."""
    return _Peg(('match(%r)', regex),
                lambda s, far, (i, vals):
                    [(_step(far, i + m.end()), vals + m.groups())
                     for m in [re.match(regex, s[i:])] if m])

def capture(p):
    """Return a peg that acts like p, except it adds to the values
    tuple the text that p matched."""
    return _Peg(('capture(%r)', p),
                lambda s, far, (i, vals):
                    [(i2, vals2 + (s[i:i2],))
                     for i2, vals2 in p.run(s, far, (i, vals))])

def feed(fn):
    """Return a peg that always succeeds, changing the values tuple
    from xs to (fn(*xs),). (We're feeding fn with the values.)"""
    return _Peg(('feed(%s)', _fn_name(fn)),
                lambda s, far, (i, vals): [(i, (fn(*vals),))])

def invert(p):
    "Return a peg that succeeds just when p fails."
    return _Peg(('invert(%r)', p),
                lambda s, far, st: [] if p.run(s, [0], st) else [st])

def either(p, q):
    """Return a peg that succeeds just when one of p or q does, trying
    them in that order."""
    return _Peg(('(%r|%r)', p, q),
                lambda s, far, st:
                    p.run(s, far, st) or q.run(s, far, st))

def chain(p, q):
    """Return a peg that succeeds when p and q both do, with q
    starting where p left off."""
    return _Peg(('(%r+%r)', p, q),
                lambda s, far, st:
                    [st3 
                     for st2 in p.run(s, far, st)
                     for st3 in q.run(s, far, st2)])

def nest(p):
    """Return a peg like p, but where p doesn't get to see or alter
    the incoming values tuple."""
    return _Peg(('nest(%r)', p),
                lambda s, far, (i, vals):
                    [(i2, vals + vals2)
                     for i2, vals2 in p.run(s, far, (i, ()))])

def maybe(p):
    "Return a peg matching 0 or 1 of what p matches."
    return label(either(p, empty),
                 '%r.maybe()', p)

def plus(p):
    "Return a peg matching 1 or more of what p matches."
    return label(chain(p, star(p)),
                 '%r.plus()', p)

def star(p):
    "Return a peg matching 0 or more of what p matches."
    return label(recur(lambda p_star: either(chain(p, p_star), empty)),
                 '%r.star()', p)

def label(p, string, *args):
    """Return an equivalent peg whose repr is (string % args), or just
    string if no args."""
    return _Peg(((string,) + args if args else string),
                p.run)

class _Peg(object):
    """A parsing expression. It can match a prefix of a sequence,
    updating a values tuple in the process, or fail."""
    def __init__(self, face, run):
        self.face = face
        self.run = run
    def __repr__(self):
        if isinstance(self.face, (str, unicode)): return self.face
        if isinstance(self.face, tuple): return self.face[0] % self.face[1:]
        assert False, "Bad face"
    def __call__(self, sequence):
        """Parse a prefix of sequence and return a tuple of values, or
        raise Unparsable."""
        far = [0]
        for i, vals in self.run(sequence, far, (0, ())):
            return vals
        raise Unparsable(self, sequence[:far[0]], sequence[far[0]:])
    def attempt(self, sequence):
        "Parse a prefix of sequence and return a tuple of values or None."
        try: return self(sequence)
        except Unparsable: return None
    def __add__(self, other):  return chain(self, Peg(other))
    def __radd__(self, other): return chain(Peg(other), self)
    def __or__(self, other):   return either(self, Peg(other))
    def __ror__(self, other):  return either(Peg(other), self)
    def __rshift__(self, fn):  return label(nest(chain(self, Peg(fn))),
                                            '(%r>>%s)', self, _fn_name(fn))
    __invert__ = invert
    maybe = maybe
    plus = plus
    star = star

class Unparsable(Exception):
    "A parsing failure."
    @property
    def position(self):
        "The rightmost position positively reached in the parse attempt."
        return len(self.args[1])
    @property
    def failure(self):  # XXX rename?
        "Return slices of the input before and after the parse failure."
        return self.args[1], self.args[2]

# TODO: need doc comments or something
fail  = _Peg('fail', lambda s, far, st: [])
empty = _Peg('empty', lambda s, far, st: [st])
             
position = _Peg('position', lambda s, far, (i, vals): [(i, vals + (i,))])
                

def _fn_name(fn):
    return fn.func_name if hasattr(fn, 'func_name') else repr(fn)

def hug(*vals):
    "Make one tuple out of any number of arguments."
    return vals

def join(*strs):
    "Make one string out of any number of string arguments."
    return ''.join(strs)

# Alternative: non-regex basic matchers, good for non-string inputs.

def one_that(ok):
    """Return a peg that eats the first element x of the input, if it
    exists and if ok(x). It leaves the values tuple unchanged.
    (N.B. the input can be a non-string: anything accessible by
    index.)"""
    def run(s, far, (i, vals)):
        try: item = s[i]
        except IndexError: return []
        return [(_step(far, i+1), vals)] if ok(item) else []
    return _Peg(('one_that(%s)', _fn_name(ok)),
                run)

def one_of(item):
    "Return a peg that eats one element equal to the argument."
    return label(one_that(lambda x: item == x),
                 'one_of(%r)', item)

someone = label(one_that(lambda x: True), 'someone')


# Parse a string representation of a grammar.

def Grammar(string):
    "XXX doc comment"
    rules, items = _parse_grammar(string)
    def bind(**subs):           # subs = substitutions
        for rule, f in items:
            rules[rule] = label(f(subs), rule)
        return _Struct(**rules)
    return bind

class _Struct(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

_default_subs = dict((k, v) for k, v in __builtins__.items() if callable(v))
_default_subs.update(dict(hug=feed(hug), join=feed(join), position=position))

def _parse_grammar(string):

    rules = {}
    refs = set()

    def mk_rule_ref(name):
        refs.add(name)
        return lambda subs: delay(lambda: rules[name], name)

    def lift(peg_op):
        return lambda *lifted: lambda subs: peg_op(*[f(subs) for f in lifted])

    unquote    = lambda name: lambda subs: Peg(subs.get(name)
                                               or _default_subs[name])

    mk_literal = lambda *cs: lambda subs: literal(''.join(cs))
    mk_match   = lambda *cs: lambda subs: match(''.join(cs))

    _              = match(r'(?:\s|#[^\n]*\n?)*')
    name           = match(r'([A-Za-z_]\w*)') +_

    regex_char     = match(r'(\\.|[^/])')
    quoted_char    = match(r'\\(.)') | match(r"([^'])")

    peg            = delay(lambda: 
                     term + '|' +_+ peg                 >> lift(either)
                   | term
                   | empty                              >> lift(lambda: empty))

    term           = delay(lambda:
                     factor + term                      >> lift(chain)
                   | factor)

    factor         = delay(lambda:
                     '~' +_+ factor                     >> lift(invert)
                   | nest(primary + (  '*' +_+             lift(star)
                                     | '+' +_+             lift(plus)
                                     | '?' +_+             lift(maybe) ).maybe()))

    primary        = ('(' +_+ peg + ')' +_
                   | '{' +_+ peg + '}' +_               >> lift(capture)
                   | "'" + quoted_char.star() + "'" +_  >> mk_literal
                   | '/' + regex_char.star() + '/' +_   >> mk_match
                   | ':' +_+ name                       >> unquote
                   | name                               >> mk_rule_ref)

    rule           = name + '=' +_+ (peg>>lift(nest)) + '.' +_ >> hug
    grammar        = _+ rule.plus() + match('$')

    try:
        items = grammar(string)
    except Unparsable, e:
        raise GrammarError("Bad grammar", e.failure)
    lhses = [L for L, R in items]
    undefined = sorted(refs - set(lhses))
    if undefined:
        raise GrammarError("Undefined rules: %s" % ', '.join(undefined))
    dups = sorted(L for L in set(lhses) if 1 != lhses.count(L))
    if dups:
        raise GrammarError("Multiply-defined rules: %s" % ', '.join(dups))
    return rules, items

class GrammarError(Exception): pass


# Smoke test: combinators

## empty
#. empty
## fail.attempt('hello')
## empty('hello')
#. ()
## match(r'(x)').attempt('hello')
## match(r'(h)')('hello')
#. ('h',)

## (match(r'(H)') | match('(.)'))('hello')
#. ('h',)
## (match(r'(h)') + match('(.)'))('hello')
#. ('h', 'e')

## (match(r'h(e)') + match(r'(.)'))('hello')
#. ('e', 'l')
## (~match(r'h(e)') + match(r'(.)'))('xhello')
#. ('x',)

## empty.run('', [0], (0, ()))
#. [(0, ())]
## chain(empty, empty)('')
#. ()

## (match(r'(.)') >> hug)('hello')
#. (('h',),)

## match(r'(.)').star()('')
#. ()

## (match(r'(.)').star())('hello')
#. ('h', 'e', 'l', 'l', 'o')

## (match(r'(.)').star() >> join)('hello')
#. ('hello',)


# Example

def make_var(v):         return v
def make_lam(v, e):      return '(lambda (%s) %s)' % (v, e)
def make_app(e1, e2):    return '(%s %s)' % (e1, e2)
def make_let(v, e1, e2): return '(let ((%s %s)) %s)' % (v, e1, e2)

eof        = match(r'$')
_          = match(r'\s*')
identifier = match(r'([A-Za-z_]\w*)\s*')

def test1():
    V     = identifier
    E     = delay(lambda: 
            V                        >> make_var
          | '\\' +_+ V + '.' +_+ E   >> make_lam
          | '(' +_+ E + E + ')' +_   >> make_app)
    start = _+ E #+ eof
    return lambda s: start(s)[0]

## test1()('x y')
#. 'x'
## test1()(r'\x.x')
#. '(lambda (x) x)'
## test1()('(x   x)')
#. '(x x)'


def test2(string):
    V     = identifier
    F     = delay(lambda: 
            V                                     >> make_var
          | '\\' +_+ V.plus() + hug + '.' +_+ E   >> fold_lam
          | '(' +_+ E + ')' +_)
    E     = F + F.star()                          >> fold_app
    start = _+ E

    vals = start.attempt(string)
    return vals and vals[0]

def fold_app(f, *fs): return reduce(make_app, fs, f)
def fold_lam(vp, e): return foldr(make_lam, e, vp)

def foldr(f, z, xs):
    for x in reversed(xs):
        z = f(x, z)
    return z

## test2('x')
#. 'x'
## test2('\\x.x')
#. '(lambda (x) x)'
## test2('(x x)')
#. '(x x)'

## test2('hello')
#. 'hello'
## test2(' x')
#. 'x'
## test2('\\x . y  ')
#. '(lambda (x) y)'
## test2('((hello world))')
#. '(hello world)'

## test2('  hello ')
#. 'hello'
## test2('hello     there hi')
#. '((hello there) hi)'
## test2('a b c d e')
#. '((((a b) c) d) e)'

## test2('')
## test2('x x . y')
#. '(x x)'
## test2('\\.x')
## test2('(when (in the)')
## test2('((when (in the)))')
#. '(when (in the))'

## test2('\\a.a')
#. '(lambda (a) a)'

## test2('  \\hello . (hello)x \t')
#. '(lambda (hello) (hello x))'

## test2('\\M . (\\f . M (f f)) (\\f . M (f f))')
#. '(lambda (M) ((lambda (f) (M (f f))) (lambda (f) (M (f f)))))'

## test2('\\a b.a')
#. '(lambda (a) (lambda (b) a))'

## test2('\\a b c . a b')
#. '(lambda (a) (lambda (b) (lambda (c) (a b))))'


# Smoke test: grammars

def exceptionally(thunk):
    try: return thunk()
    except Exception, e: return e

## exceptionally(lambda: Grammar(r"a = . b = a. a = .")())
#. GrammarError('Multiply-defined rules: a',)

## exceptionally(lambda: Grammar(r"a = b|c|d. c = .")())
#. GrammarError('Undefined rules: b, d',)

## exceptionally(lambda: Grammar(r"a = ")())
#. GrammarError('Bad grammar', ('a = ', ''))

nums = Grammar(r"""
# This is a comment.
main = nums /$/.  # So's this.

nums = num ',' nums
     | num
     | .

num  = /([0-9]+)/ :int.
""")()
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
## nums.main.attempt('10,30,43 xxx')


gsub_grammar = Grammar(r"""
gsub = (:p :replace | /(.)/) gsub | .
""")
def gsub(text, p, replacement):
    g = gsub_grammar(p=p, replace=lambda: replacement)
    return ''.join(g.gsub(text))
## gsub('hi there WHEEWHEE to you WHEEEE', 'WHEE', 'GLARG')
#. 'hi there GLARGGLARG to you GLARGEE'
