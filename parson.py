"""
Parsing with PEGs.
"""

import re, types

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

def maybe(p):
    "Return a peg matching 0 or 1 of what p matches."
    return label(either(p, empty),
                 '(%r)?', p)

def plus(p):
    "Return a peg matching 1 or more of what p matches."
    return label(chain(p, star(p)),
                 '(%r)+', p)

def star(p):
    "Return a peg matching 0 or more of what p matches."
    return label(recur(lambda p_star: maybe(chain(p, p_star))),
                 '(%r)*', p)

def invert(p):
    "Return a peg that succeeds just when p fails."
    return _Peg(('!(%r)', p),
                lambda s, far, st: [] if p.run(s, [0], st) else [st])

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
        for _, vals in self.run(sequence, far, (0, ())):
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
    def __rshift__(self, fn):  return label(seclude(chain(self, Peg(fn))),
                                            '(%r>>%s)', self, _fn_name(fn))
    __invert__ = invert
    maybe = maybe
    plus = plus
    star = star

def _fn_name(fn):
    return fn.func_name if hasattr(fn, 'func_name') else repr(fn)

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

def label(p, string, *args):
    """Return an equivalent peg whose repr is (string % args), or just
    string if no args."""
    return _Peg(((string,) + args if args else string),
                p.run)

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

# TODO: need doc comments or something
fail  = _Peg('fail', lambda s, far, st: [])
empty = label(~fail, 'empty')
             
position = _Peg('position', lambda s, far, (i, vals): [(i, vals + (i,))])
                
def literal(string):
    "Return a peg that matches string exactly."
    return label(match(re.escape(string)),
                 'literal(%r)', string)

def match(regex):
    """Return a peg that matches what regex does, adding any captures
    to the values tuple."""
    compiled = re.compile(regex)
    return _Peg(('/%s/', regex),
                lambda s, far, (i, vals):
                    [(_step(far, m.end()), vals + m.groups())
                     for m in [compiled.match(s, i)] if m])

def _step(far, i):
    "Update far with a new position."
    far[0] = max(far[0], i)
    return i

def capture(p):
    """Return a peg that acts like p, except it adds to the values
    tuple the text that p matched."""
    return _Peg(('capture(%r)', p),
                lambda s, far, (i, vals):
                    [(i2, vals2 + (s[i:i2],))
                     for i2, vals2 in p.run(s, far, (i, vals))])

def seclude(p):
    """Return a peg like p, but where p doesn't get to see or alter
    the incoming values tuple."""
    return _Peg(('[%r]', p),
                lambda s, far, (i, vals):
                    [(i2, vals + vals2)
                     for i2, vals2 in p.run(s, far, (i, ()))])

def either(p, q):
    """Return a peg that succeeds just when one of p or q does, trying
    them in that order."""
    return _Peg(('(%r|%r)', p, q),
                lambda s, far, st:
                    p.run(s, far, st) or q.run(s, far, st))

def chain(p, q):
    """Return a peg that succeeds when p and q both do, with q
    starting where p left off."""
    return _Peg(('(%r %r)', p, q),
                lambda s, far, st:
                    [st3 
                     for st2 in p.run(s, far, st)
                     for st3 in q.run(s, far, st2)])

def alter(fn):                  # XXX better name
    """Return a peg that always succeeds, changing the values tuple
    from xs to fn(*xs)."""
    return _Peg(('alter(%s)', _fn_name(fn)),
                lambda s, far, (i, vals): [(i, fn(*vals))])  # XXX check that result is tuple?

def feed(fn):
    """Return a peg that always succeeds, changing the values tuple
    from xs to (fn(*xs),). (We're feeding fn with the values.)"""
    return label(alter(lambda *vals: (fn(*vals),)),
                 ':%s', _fn_name(fn))

def push(c):
    return label(alter(lambda *xs: xs + (c,)),
                 'push(%r)' % (c,),)
                 
def trace(message):
    "A peg that succeeds, and says so."
    # TODO: better debugging means
    def tracer(s, far, (i, vals)):
        print message, i, vals
        return [(i, vals)]
    return P._Peg('trace', tracer)


# Some often-useful actions for feed().

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
    return _Peg(('one_that(%s)', _fn_name(ok)), run)

def one_of(item):
    "Return a peg that eats one element equal to the argument."
    return label(one_that(lambda x: item == x),
                 'one_of(%r)', item)

anyone = label(one_that(lambda x: True), 'anyone')


# Non-strings can include nested sequences:

def nest(p):
    "Return a peg that eats one item, a sequence that p eats a prefix of."
    def run(s, far, (i, vals)):
        try: item = s[i]
        except IndexError: return []
        if not _is_indexable(item): return []
        return [(_step(far, i+1), vals1)
                for _, vals1 in p.run(item, [0], (0, vals))]
    return _Peg(('nest(%r)', p), run)

def _is_indexable(x):
    try: x[0]
    except TypeError: return False
    except KeyError: return False
    except IndexError: return True
    return True

## (nest(one_of(1)) + one_of(5)).attempt([1, 5])
## (nest(one_of(1)) + one_of(5)).attempt([[1], 5])
#. ()


# Build pegs from a string representation of a grammar.

class Grammar(object):
    """XXX doc comment
    Contrived example:
    >>> g = Grammar(r"a = 'x'|b.   b = !:p /regex/.  # comment")(p=fail)
    >>> g.a('x')
    ()
    """
    def __init__(self, string):
        self.skeletons = _parse_grammar(string)
    def __call__(self, **subs):
        return self.bind(subs)
    def bind(self, subs):       # subs = substitutions
        if isinstance(subs, types.ModuleType):
            subs = subs.__dict__
        rules = {}
        for rule, (_,f) in self.skeletons:
            rules[rule] = label(f(rules, subs), rule)
        # XXX warn about unresolved :foo interpolations at this point?
        return _Struct(**rules)

class _Struct(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def _parse_grammar(string):
    try:
        skeletons = _grammar_grammar(string)
    except Unparsable, e:
        raise GrammarError("Bad grammar", e.failure)
    lhses = [L for L, R in skeletons]
    all_refs = set().union(*[refs for L, (refs,_) in skeletons])
    undefined = sorted(all_refs - set(lhses))
    if undefined:
        raise GrammarError("Undefined rules: %s" % ', '.join(undefined))
    dups = sorted(L for L in set(lhses) if 1 != lhses.count(L))
    if dups:
        raise GrammarError("Multiply-defined rules: %s" % ', '.join(dups))
    return skeletons

class GrammarError(Exception): pass

_builtins = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
_default_subs = dict((k, feed(v))
                     for k, v in _builtins.items() if callable(v))
_default_subs.update({'hug': feed(hug), 'join': feed(join), 'None': push(None),
                      'position': position})

def _lookup(subs, name):
    # We don't use subs.get(name) because subs might be a dictlike object
    # that manufactures a value for any name, in which case it'd be a 
    # nuisance for that subs object to have to implement get() too.
    try:
        return subs[name]
    except KeyError:
        return _default_subs[name]

def _make_grammar_grammar():

    def mk_rule_ref(name):
        return (set([name]),
                lambda rules, subs: delay(lambda: rules[name], name))

    def constant(peg): return (set(), lambda rules, subs: peg)

    def lift(peg_op):
        return lambda *lifted: (
            set().union(*[refs for refs,_ in lifted]),
            lambda rules, subs: peg_op(*[f(rules, subs) for _,f in lifted])
        )

    unquote     = lambda name: (set(), lambda rules, subs: Peg(_lookup(subs, name)))

    mk_literal  = lambda string: constant(literal(string))
    mk_push_lit = lambda string: constant(push(string))
    mk_match    = lambda *cs: constant(match(''.join(cs)))

    _              = match(r'(?:\s|#[^\n]*\n?)*')   # Whitespace and comments
    name           = match(r'([A-Za-z_]\w*)') +_
    word           = match(r'(\w+)') +_

    regex_char     = match(r'(\\.|[^/])')
    quoted_char    = match(r'\\(.)') | match(r"([^'])")

    qstring        = "'" + quoted_char.star() + "'" +_  >> join

    pe             = seclude(delay(lambda: 
                     term + ('|' +_+ pe + lift(either)).maybe()
                   | lift(lambda: empty)))

    term           = seclude(delay(lambda:
                     factor + (term + lift(chain)).maybe()))

    factor         = seclude(delay(lambda:
                     '!' +_+ factor                     + lift(invert)
                   | primary + ( '*' +_+ lift(star)
                               | '+' +_+ lift(plus)
                               | '?' +_+ lift(maybe)
                               ).maybe()))

    primary        = ('(' +_+ pe + ')' +_
                   | '[' +_+ pe + ']' +_                >> lift(seclude)
                   | '{' +_+ pe + '}' +_                >> lift(capture)
                   | qstring                            >> mk_literal
                   | '/' + regex_char.star() + '/' +_   >> mk_match
                   | ':' +_+ ( word                     >> unquote
                             | qstring                  >> mk_push_lit)
                   | name                               >> mk_rule_ref)

    rule           = seclude(
                     name + ('=' +_+ pe
                             | ':' +_+ (pe >> lift(seclude)))
                     + '.' +_ + hug)
    grammar        = _+ rule.plus() + ~anyone

    return grammar

_grammar_grammar = _make_grammar_grammar()


# To help testing. (XXX move this out of the main library)
def exceptionally(thunk):
    try: return thunk()
    except Exception, e: return e
