"""
A PEG parser using explicit control instead of recursion.
Avoids Python stack overflow.
Also a step towards compiling instead of interpreting.

to do: test this: optimize q==y with Nip
to do: produce code instead of closures
to do: bounce less often

to do: compare:
  (Knuth 1971), Donald Knuth describes an abstract parsing machine. This
  machine runs programs in which the instructions either recognize and
  con- sume a token from the input, or call a subroutine to recognize an
  instance of a non-terminal. Each instruction has two continuations for
  success and failure, and part of the subroutine mechanism is that if a
  subroutine returns with failure, then the input pointer is reset to
  where it was when the subrou- tine was called. A subroutine that
  returns successfully, however, deletes the record of the old position
  of the input pointer. There is a natural translation of context-free
  grammars into programs for this machine, which behave ex- actly like
  combinator parsers based on Maybe.
"""

dbg = 1

# peg constructors

Fail = 'fail', ()
def Alter(fn):     return 'alter', fn
def Item(ok):      return 'item', ok
def Ref(name):     return 'ref', name
def Chain(q, r):   return 'chain', (q, r)
def Cond(q, n, y): return 'cond', (q, n, y)


# (install, program, peg, fail_cont, success_cont) -> cont
# where program: dict(string -> cont)
#       code: [('operator', (operands,))]
#       cont: int -- index into code
def translate(install, pr, peg, f, s):
    tag, arg = peg
    if   tag == 'fail':  return install(KDrop, f) 
    elif tag == 'alter': return install(KAlter, arg, s)
    elif tag == 'item':  return install(KItem, arg, f, s)
    elif tag == 'ref':   return install(KCall, pr, arg, f, s) # TODO: how about a jump op for when f is KFail, s is KSucceed?
    elif tag == 'chain': return translate(install, pr, arg[0], f,
                                          translate(install, pr, arg[1], f, s))
    elif tag == 'cond':
        q, n, y = arg
        if y == q:
            yy = install(KNip, s)
        elif y[0] == 'chain' and y[1][0] == q:
            yy = install(KNip, translate(install, pr, y[1][1], f, s))
        else:
            yy = install(KDrop, translate(install, pr, y, f, s))
        return install(KDup, translate(install, pr, q, translate(install, pr, n, f, s), yy))
    else:
        assert False

def run(q, defns, vs, cs):
    code = []
    def install(*insn):
        try: return code.index(insn)
        except ValueError:
            try: return len(code)
            finally: code.append(insn)
    pr = {}
    entry = translate(install, pr, q, install(KFinalFail), install(KFinalSucceed))
    for name, defn in defns.items():
        pr[name] = translate(install, pr, defn, install(KFail), install(KSucceed))
    if dbg:
        for name in sorted(pr.keys()):
            print name, '=>', pr[name]
        for i, insn in enumerate(code):
            print i, show(insn)
    return trampoline(entry, code,
                      ((vs,cs,()), ()))

def show(insn):
    return '%s(%s)' % (insn[0].__name__,
                       ', '.join(x.__name__ if callable(x) else repr(x)
                                 for x in insn[1:]))

# The parsing machine.
# continuation: trail -> result
# trail: () | ((vs,cs,ks), trail)
# vs: tuple of values from semantic actions
# cs: input character sequence (the current tail thereof)
# ks: () | ((fail_cont,success_cont), ks)

def trampoline(pc, code, trail):
    while pc is not None:
        insn = code[pc]
        if dbg: print 'pc', pc, 'insn', show(insn)
        pc, trail = insn[0](*insn[1:])(trail)
        assert pc is None or isinstance(pc, int), pc
    return trail

def KFinalFail():
    def k(trail):
        assert trail is ()
        return None, 'fail'
    return k
def KFinalSucceed():
    def k(((vs,cs,ks), trail)):
        assert trail is ()
        assert ks is ()
        return None, (vs, cs)
    return k

def KDrop(cont): return lambda (_, trail): (cont, trail)
def KNip(cont): return lambda (entry, (_, trail)): (cont, (entry, trail))
def KDup(cont): return lambda (entry, trail): (cont, (entry, (entry, trail)))

def KAlter(fn, s):
    return lambda ((vs,cs,ks), trail): (s, ((fn(*vs),cs,ks), trail))

def KItem(ok, f, s):
    return lambda ((vs,cs,ks), trail): (
        (s, ((vs+(cs[0],), cs[1:], ks), trail)) if cs and ok(cs[0])
        else (f, trail))

def KCall(pr, name, f, s):
    return lambda ((vs,cs,ks), trail): (
        pr[name], ((vs,cs,((f,s),ks)), trail))
def KFail():
    return lambda ((vs,cs,((fk,_),ks)), trail): (fk, trail)
def KSucceed():
    return lambda ((vs,cs,((_,sk),ks)), trail): (sk, ((vs,cs,ks), trail))


# Smoke test

def Lit(c):
    def t(c1): return c == c1
    t.__name__ = 'eq %r' % c
    return Item(t)
def Or(q, r): return Cond(q, r, q)
def identity(*vals): return vals
# XXX is this really equivalent to a 'native' Or. As a tail call, too.
Succeed = Alter(identity)

bit = Or(Lit('0'), Lit('1'))
twobits = Chain(bit, bit)

nbits_defs = {'nbits': Cond(bit, Succeed, Chain(bit, Ref('nbits')))}

def test(string):
#    return run(Lit('0'), (), string)
#    return run(bit, (), string)
#    return run(twobits, {}, (), string)
    return run(Ref('nbits'), nbits_defs, (), string)

## test('xy')
#. nbits => 12
#. 0 KFinalFail()
#. 1 KFinalSucceed()
#. 2 KCall({'nbits': 12}, 'nbits', 0, 1)
#. 3 KFail()
#. 4 KSucceed()
#. 5 KCall({'nbits': 12}, 'nbits', 3, 4)
#. 6 KNip(5)
#. 7 KAlter(identity, 4)
#. 8 KNip(6)
#. 9 KItem(eq '1', 7, 6)
#. 10 KItem(eq '0', 9, 8)
#. 11 KDup(10)
#. 12 KDup(11)
#. pc 2 insn KCall({'nbits': 12}, 'nbits', 0, 1)
#. pc 12 insn KDup(11)
#. pc 11 insn KDup(10)
#. pc 10 insn KItem(eq '0', 9, 8)
#. pc 9 insn KItem(eq '1', 7, 6)
#. pc 7 insn KAlter(identity, 4)
#. pc 4 insn KSucceed()
#. pc 1 insn KFinalSucceed()
#. ((), 'xy')
## test('01101a')
#. nbits => 12
#. 0 KFinalFail()
#. 1 KFinalSucceed()
#. 2 KCall({'nbits': 12}, 'nbits', 0, 1)
#. 3 KFail()
#. 4 KSucceed()
#. 5 KCall({'nbits': 12}, 'nbits', 3, 4)
#. 6 KNip(5)
#. 7 KAlter(identity, 4)
#. 8 KNip(6)
#. 9 KItem(eq '1', 7, 6)
#. 10 KItem(eq '0', 9, 8)
#. 11 KDup(10)
#. 12 KDup(11)
#. pc 2 insn KCall({'nbits': 12}, 'nbits', 0, 1)
#. pc 12 insn KDup(11)
#. pc 11 insn KDup(10)
#. pc 10 insn KItem(eq '0', 9, 8)
#. pc 8 insn KNip(6)
#. pc 6 insn KNip(5)
#. pc 5 insn KCall({'nbits': 12}, 'nbits', 3, 4)
#. pc 12 insn KDup(11)
#. pc 11 insn KDup(10)
#. pc 10 insn KItem(eq '0', 9, 8)
#. pc 9 insn KItem(eq '1', 7, 6)
#. pc 6 insn KNip(5)
#. pc 5 insn KCall({'nbits': 12}, 'nbits', 3, 4)
#. pc 12 insn KDup(11)
#. pc 11 insn KDup(10)
#. pc 10 insn KItem(eq '0', 9, 8)
#. pc 9 insn KItem(eq '1', 7, 6)
#. pc 6 insn KNip(5)
#. pc 5 insn KCall({'nbits': 12}, 'nbits', 3, 4)
#. pc 12 insn KDup(11)
#. pc 11 insn KDup(10)
#. pc 10 insn KItem(eq '0', 9, 8)
#. pc 8 insn KNip(6)
#. pc 6 insn KNip(5)
#. pc 5 insn KCall({'nbits': 12}, 'nbits', 3, 4)
#. pc 12 insn KDup(11)
#. pc 11 insn KDup(10)
#. pc 10 insn KItem(eq '0', 9, 8)
#. pc 9 insn KItem(eq '1', 7, 6)
#. pc 6 insn KNip(5)
#. pc 5 insn KCall({'nbits': 12}, 'nbits', 3, 4)
#. pc 12 insn KDup(11)
#. pc 11 insn KDup(10)
#. pc 10 insn KItem(eq '0', 9, 8)
#. pc 9 insn KItem(eq '1', 7, 6)
#. pc 7 insn KAlter(identity, 4)
#. pc 4 insn KSucceed()
#. pc 4 insn KSucceed()
#. pc 4 insn KSucceed()
#. pc 4 insn KSucceed()
#. pc 4 insn KSucceed()
#. pc 4 insn KSucceed()
#. pc 1 insn KFinalSucceed()
#. (('0', '1', '1', '0', '1'), 'a')
