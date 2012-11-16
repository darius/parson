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
    """Make a peg from a Python value as appropriate for its type, as
    a convenience. For a string, that's a regex matcher; for a function
    it's a feed action (transform the current values tuple)."""
    if isinstance(x, _Peg):           return x
    if isinstance(x, (str, unicode)): return literal(x)
    if callable(x):                   return feed(x)
    raise ValueError("Not a Peg", x)

def recur(fn, face=None):
    "Return a peg p such that p = fn(p). This is like the Y combinator."
    p = delay(lambda: fn(p), face or (lambda: 'recur(%s)' % _fn_name(fn)))
    return p

def delay(thunk, face=None):
    """Precondition: thunk() will return a peg p. We immediately
    return a peg q equivalent to that future p, but we'll call thunk()
    only once, and not until the first use of q. Use this for
    recursive grammars."""
    def run(s, far, st):
        q.run = Peg(thunk()).run
        return q.run(s, far, st)
    q = _Peg(run, face or (lambda: 'delay(%s)' % _fn_name(thunk)))
    return q

def _step(far, i):
    "Update far with the new position, i."
    far[0] = max(far[0], i)
    return i

def literal(string):
    "Return a peg that matches string exactly."
    return match(re.escape(string))

def match(regex):
    """Return a peg that matches what regex does, adding any captures
    to the values tuple."""
    return _Peg(lambda s, far, (i, vals):
                    [(_step(far, i + m.end()), vals + m.groups())
                     for m in [re.match(regex, s[i:])] if m],
                lambda: 'match(%r)' % regex)

def feed(fn):
    """Return a peg that always succeeds, changing the values tuple
    from xs to (fn(*xs),). (We're feeding fn with the values.)"""
    return _Peg(lambda s, far, (i, vals): [(i, (fn(*vals),))],
                lambda: 'feed(%s)' % _fn_name(fn))

def capture(p):
    """Return a peg that acts like p, except it adds to the values
    tuple the text that p matched."""
    return _Peg(lambda s, far, (i, vals):
                    [(i2, vals2 + (s[i:i2],))
                     for i2, vals2 in p.run(s, far, (i, vals))],
                lambda: 'capture(%r)' % (p,))

def invert(p):
    "Return a peg that succeeds just when p fails."
    return _Peg(lambda s, far, st: [] if p.run(s, [0], st) else [st],
                lambda: 'invert(%r)' % (p,))

def either(p, q, face=None):
    """Return a peg that succeeds just when one of p or q does, trying
    them in that order."""
    return _Peg(lambda s, far, st: p.run(s, far, st) or q.run(s, far, st),
                face or (lambda: '(%r|%r)' % (p, q)))

def chain(p, q, face=None):
    """Return a peg that succeeds when p and q both do, with q
    starting where p left off."""
    return _Peg(lambda s, far, st:
                    [st3 
                     for st2 in p.run(s, far, st)
                     for st3 in q.run(s, far, st2)],
                face or (lambda: '(%r+%r)' % (p, q)))

def nest(p, face=None):
    """Return a peg like p, but where p doesn't get to see or alter
    the incoming values tuple."""
    return _Peg(lambda s, far, (i, vals):
                    [(i2, vals + vals2)
                     for i2, vals2 in p.run(s, far, (i, ()))],
                face or (lambda: 'nest(%r)' % (p,)))

def maybe(p):
    "Return a peg matching 0 or 1 of what p matches."
    return either(p, empty, lambda: '(%r).maybe()' % (p,))

def plus(p):
    "Return a peg matching 1 or more of what p matches."
    return chain(p, star(p), lambda: '(%r).plus()' % (p,))

def star(p):
    "Return a peg matching 0 or more of what p matches."
    return recur(lambda p_star: either(chain(p, p_star), empty),
                 lambda: '(%r).star()' % (p,))

class _Peg(object):
    """A parsing expression. It can match a prefix of a sequence,
    updating a values tuple in the process, or fail."""
    def __init__(self, run, face=None):
        self.run = run
        self.face = face
    def __repr__(self):
        return self.face() if self.face else object.__repr__(self)
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
    def __rshift__(self, fn):  return nest(chain(self, Peg(fn)),
                                           lambda: '(%r>>%s)' % (self,
                                                                 _fn_name(fn)))
    __invert__ = invert
    maybe = maybe
    plus = plus
    star = star

class Unparsable(Exception):
    """A parsing failure."""
    @property
    def position(self):
        "The rightmost position positively reached in the parse attempt."
        return len(self.args[1])

# TODO: need doc comments or something
fail  = _Peg(lambda s, far, st: [],
             lambda: 'fail')
empty = _Peg(lambda s, far, st: [st],
             lambda: 'empty')

position = _Peg(lambda s, far, (i, vals): [(i, vals + (i,))],
                lambda: 'position')

def _fn_name(f):
    return f.func_name if hasattr(f, 'func_name') else repr(f)

def hug(*vals):
    "Make one tuple out of any number of arguments."
    return vals

def join(*strs):
    "Make one string out of any number of string arguments."
    return ''.join(strs)

# Alternative: non-regex basic matchers

def one_that(ok, face=None):
    """Return a peg that eats the first element x of the input, if it
    exists and if ok(x). It leaves the values tuple unchanged.
    (N.B. the input can be a non-string.)"""
    return _Peg((lambda s, far, (i, vals):
        [(_step(far, i+1), vals)] if i < len(s) and ok(s[i]) else []),
                face or (lambda: 'one_that(%s)' % _fn_name(ok)))

someone = one_that(lambda x: True, lambda: 'someone')

def one_of(item):
    "Return a peg that eats one element equal to the argument."
    return one_that(lambda x: item == x,
                    lambda: 'one_of(%r)' % (item,))


# Smoke test

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
    return vals[0] if vals else None

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
