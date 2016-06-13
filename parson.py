"""
Parsing with PEGs.
"""

import collections, re, types

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

def plus(p, separator=None):
    "Return a peg matching 1 or more of what p matches (maybe with separator)."
    if separator is None:
        return label(chain(p, star(p)),
                     '(%r)+', p)
    else:
        return label(chain(p, star(chain(separator, p))),
                     '(%r)++(%r)', p, separator)

def star(p, separator=None):
    "Return a peg matching 0 or more of what p matches (maybe with separator)."
    if separator is None:
        # p* = (p p*)?
        return label(recur(lambda p_star: maybe(chain(p, p_star))),
                     '(%r)*', p)
    else:
        # p**sep = (p (sep p)*)?
        return label(maybe(chain(p, star(chain(separator, p)))),
                     '(%r)**(%r)', p, separator)

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
    def __rrshift__(self, lhs): return Peg(lhs) >> self
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
end = label(~anyone, 'end')


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
    """XXX doc comment"""
    def __init__(self, string):
        self.skeletons = _parse_grammar(string)
    def __call__(self, **subs):
        return self.bind(subs)
    def bind(self, subs):       # subs = substitutions
        if isinstance(subs, types.ModuleType):
            subs = subs.__dict__
        result = None
        rules = {name: delay(lambda: rules[name], name)
                 for (name,_,_) in self.skeletons if name is not None}
        for rule, fnord_rule_type, (_,f) in self.skeletons:
            peg = f(self, rules, fnord_rule_type == '', subs)
            if rule is None:
                result = peg
            else:
                rules[rule] = label(peg, rule)
        # XXX warn about unresolved :foo interpolations at this point?
        if result is None:
            result = _Struct()
        result.__dict__.update(rules)
        return result
    def literal(self, string):
        return literal(string)
    def match(self, regex):
        return match(regex)
    def keyword(self, string):
        return literal(string) + word_boundary

word_boundary = match(r'\b')

class _Struct(object): pass

def _parse_grammar(string):
    try:
        skeletons = _grammar_grammar(string)
    except Unparsable, e:
        raise GrammarError("Bad grammar", e.failure)
    lhses = [L for L, _, R in skeletons]
    all_refs = set().union(*[refs for L, _, (refs,_) in skeletons])
    undefined = sorted(all_refs - set(lhses))
    if undefined:
        raise GrammarError("Undefined rules: %s" % ', '.join(undefined))
    counts = collections.Counter(lhses)
    dups = sorted(lhs for lhs,n in counts.items() if 1 < n)
    if dups:
        raise GrammarError("Multiply-defined rules: %s" % ', '.join(dups))
    return skeletons

class GrammarError(Exception): pass

_builtins = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
_default_subs = dict((k, feed(v))
                     for k, v in _builtins.items() if callable(v))
_default_subs.update({'hug': feed(hug), 'join': feed(join), 'None': push(None),
                      'anyone': anyone, 'end': end, 'position': position})

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
                lambda builder, rules, af, subs: delay(lambda: rules[name], name))

    def constant(peg): return (set(), lambda builder, rules, af, subs: peg)

    def lift(peg_op):
        return lambda *lifted: (
            set().union(*[refs for refs,_ in lifted]),
            lambda builder, rules, af, subs: peg_op(*[f(builder, rules, af, subs)
                                                      for _,f in lifted])
        )

    def mk_fnordly((refs, mk_peg)):
        def mk_result(builder, rules, allow_fnord, subs):
            result = mk_peg(builder, rules, allow_fnord, subs)
            if allow_fnord and 'FNORD' in rules:
                # N.B. we don't add FNORD to refs; it won't matter.
                result = chain(result, delay(lambda: rules['FNORD'], 'FNORD'))
            return result
        return (refs, mk_result)

    unquote     = lambda name: (set(), lambda _, rules, af, subs: Peg(_lookup(subs, name)))

    mk_push_lit = lambda string: constant(push(string))

    def mk_literal(s): return (set(), lambda builder, _, __, ___: builder.literal(s))
    def mk_keyword(s): return (set(), lambda builder, _, __, ___: builder.keyword(s))
    def mk_match(s):   return (set(), lambda builder, _, __, ___: builder.match(s))

    whitespace     = match(r'(?:\s|#[^\n]*\n?)+')
    _              = whitespace.maybe()
    name           = match(r'([A-Za-z_]\w*)') +_
    word           = match(r'(\w+)') +_

    regex_char     = match(r'(\\.|[^/])')
    quoted_char    = match(r'\\(.)') | match(r"([^'])") # XXX understand escapes like \n
    dquoted_char   = match(r'\\(.)') | match(r'([^"])')

    qstring        = "'" +  quoted_char.star() + "'" +_  >> join
    dqstring       = '"' + dquoted_char.star() + '"' +_  >> join

    fnordly        = (literal('~') + _) | mk_fnordly

    pe             = seclude(delay(lambda: 
                     term + ('|' +_+ pe + lift(either)).maybe()
                   | lift(lambda: empty)))

    term           = seclude(delay(lambda:
                     factor + (term + lift(chain)).maybe()))

    factor         = seclude(delay(lambda:
                     '!' +_+ factor                     + lift(invert)
                   | primary + ( '**' +_+ primary + lift(star)
                               | '++' +_+ primary + lift(plus)
                               | '*' +_+ lift(star)
                               | '+' +_+ lift(plus)
                               | '?' +_+ lift(maybe)
                               ).maybe()))

    primary        = ('(' +_+ pe + ')' +_
                   | '[' +_+ pe + ']' +_                >> lift(seclude)
                   | '{' +_+ pe + '}' +_                >> lift(capture)
                   | seclude(qstring + mk_literal + fnordly)
                   | seclude(dqstring + mk_keyword + fnordly)
                   | seclude('/' + regex_char.star() + '/' +_+ join + mk_match + fnordly)
                   | ':' + ( word                       >> unquote
                           | qstring                    >> mk_push_lit)
                   | name                               >> mk_rule_ref)

    rule           = seclude(
                     name + match('(~?)') + _
                     + ('=' +_+ pe
                       | ':' + whitespace # Whitespace is *required* after this ':',
                                          # and *forbidden* after the ':' in 'primary'.
                         + (pe >> lift(seclude)))
                     + '.' +_ + hug)

    anon           = (push(None)
                      + push('')
                      + seclude(push('') + mk_literal + fnordly + pe + lift(chain))
                      + hug
                      + ('.' +_+ rule.star()).maybe())

    grammar        = _+ (  rule.plus() + end
                         | anon + end)

    return grammar

_grammar_grammar = _make_grammar_grammar()


# To help testing. (XXX move this out of the main library)
def exceptionally(thunk):
    try: return thunk()
    except Exception, e: return e
