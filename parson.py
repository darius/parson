import re

# Glossary:
#   p, q	peg
#   s		subject sequence
#   i           position in subject sequence
#   far         box holding the rightmost position reached so far
#   vals        values tuple
#   fn          function (not a peg)

def Peg(x):
    if isinstance(x, _Peg):           return x
    if isinstance(x, (str, unicode)): return match(x)
    if callable(x):                   return chop(x)
    raise ValueError("Not a Peg", x)

class _Peg(object):
    def __init__(self, run):
        self.run = run
    def __call__(self, sequence):
        far = [0]
        for i, vals in self.run(sequence, far, (0, ())):
            return vals
        raise Unparsable(self, (sequence[:far[0]], sequence[far[0]:]))
    def match(self, sequence):
        try: return self(sequence)
        except Unparsable: return None
    def __add__(self, other):  return seq(self, Peg(other))
    def __radd__(self, other): return seq(Peg(other), self)
    def __or__(self, other):   return alt(self, Peg(other))
    def __ror__(self, other):  return alt(Peg(other), self)
    def __invert__(self):      return invert(self)
    def __rshift__(self, fn):  return nest(seq(self, Peg(fn)))
    def maybe(self): return alt(self, empty)
    def plus(self): return seq(self, self.star())
    def star(self): return recur(lambda starred: alt(seq(self, starred), empty))

class Unparsable(Exception): pass

def recur(fn):
    p = delay(lambda: fn(p))
    return p

def delay(thunk, face=None):    # fill in or delete
    def run(s, far, st):
        p.run = left_recursion
        p.run = Peg(thunk()).run
        return p.run(s, far, st)
    p = _Peg(run)
    return p

def left_recursion(s, far, st):
    assert False, "Left recursion detected"

def step(far, i):
    far[0] = max(far[0], i)
    return i

fail  = _Peg(lambda s, far, st: [])
empty = _Peg(lambda s, far, st: [st])

position = _Peg(lambda s, far, (i, vals): [(i, vals + (i,))])

def match(regex):
    return _Peg(lambda s, far, (i, vals):
                    [(step(far, i + m.end()), vals + m.groups())
                     for m in [re.match(regex, s[i:])] if m])

def chop(fn):
    return _Peg(lambda s, far, (i, vals): [(i, (fn(*vals),))])

def catch(p):
    return _Peg(lambda s, far, (i, vals):
                    [(i2, vals2 + (s[i:i2],))
                     for i2, vals2 in p.run(s, far, (i, vals))])

def invert(p):
    return _Peg(lambda s, far, st: [] if p.run(s, [0], st) else [st])

def alt(p, q):
    return _Peg(lambda s, far, st: p.run(s, far, st) or q.run(s, far, st))

def seq(p, q):
    return _Peg(lambda s, far, st:
                    [st3 
                     for st2 in p.run(s, far, st)
                     for st3 in q.run(s, far, st2)])

def nest(p):
    return _Peg(lambda s, far, (i, vals):
                    [(i2, vals + vals2)
                     for i2, vals2 in p.run(s, far, (i, ()))])

chunk = lambda *vals: vals
cat = lambda *strs: ''.join(strs)

# Alternative: non-regex basic matchers

def check(ok):
    return _Peg(lambda s, far, (i, vals):
        [(step(far, i+1), vals)] if i < len(s) and ok(s[i]) else [])

any = check(lambda x: True)
def lit(element): return check(lambda x: element == x)


# Smoke test

## fail.match('hello')
## empty('hello')
#. ()
## Peg(r'(x)').match('hello')
## Peg(r'(h)')('hello')
#. ('h',)

## (Peg(r'(H)') | '(.)')('hello')
#. ('h',)
## (Peg(r'(h)') + '(.)')('hello')
#. ('h', 'e')

## (Peg(r'h(e)') + r'(.)')('hello')
#. ('e', 'l')
## (~Peg(r'h(e)') + r'(.)')('xhello')
#. ('x',)

## empty.run('', [0], (0, ()))
#. [(0, ())]
## seq(empty, empty)('')
#. ()

## (match(r'(.)') >> chunk)('hello')
#. (('h',),)

## match(r'(.)').star()('')
#. ()

## (match(r'(.)').star())('hello')
#. ('h', 'e', 'l', 'l', 'o')

## (match(r'(.)').star() >> cat)('hello')
#. ('hello',)


# Example

def make_var(v):         return v
def make_lam(v, e):      return '(lambda (%s) %s)' % (v, e)
def make_app(e1, e2):    return '(%s %s)' % (e1, e2)
def make_let(v, e1, e2): return '(let ((%s %s)) %s)' % (v, e1, e2)

eof        = Peg(r'$')
_          = Peg(r'\s*')
identifier = Peg(r'([A-Za-z_]\w*)\s*')

def test1():
    V     = identifier
    E     = delay(lambda: 
            V                            >> make_var
          | r'\\' +_+ V + '[.]' +_+ E    >> make_lam
          | '[(]' +_+ E + E + '[)]' +_   >> make_app)
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
            V                                  >> make_var
          | r'\\' +_+ V.plus() + chunk + '[.]' +_+ E   >> fold_lam
          | '[(]' +_+ E + '[)]' +_)
    E     = F + F.star()                       >> fold_app
    start = _+ E

    vals = start.match(string)
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

