"""
A PEG parser using explicit control instead of recursion.
Avoids Python stack overflow.
Also a step towards compiling instead of interpreting.

to do: test this: optimize q==y with Nip
to do: produce code instead of closures
to do: bounce less often
"""

# peg constructors

Fail = 'fail', None
def Alter(fn):     return 'alter', fn
def Item(ok):      return 'item', ok
def Ref(name):     return 'ref', name
def Chain(q, r):   return 'chain', (q, r)
def Cond(q, n, y): return 'cond', (q, n, y)


# (program, peg, fail_cont, success_cont) -> cont
# where program: dict(string -> cont)

def translate(pr, peg, f, s):
    tag, arg = peg
    if tag == 'fail':    return KDrop(f) 
    elif tag == 'alter': return KAlter(arg, s)
    elif tag == 'item':  return KItem(arg, f, s)
    elif tag == 'ref':   return KCall(pr, arg, f, s)
    elif tag == 'chain': return translate(pr, arg[0], f,
                                          translate(pr, arg[1], f, s))
    elif tag == 'cond':
        q, n, y = arg
        if y == q:
            yy = KNip(s)
        elif y[0] == 'chain' and y[1][0] == q:
            yy = KNip(translate(pr, y[1][1], f, s))
        else:
            yy = KDrop(translate(pr, y, f, s))
        return KDup(translate(pr, q, translate(pr, n, f, s), yy))
    else:
        assert False

def run(q, defns, vs, cs):
    pr = {}
    for name, defn in defns.items():
        pr[name] = translate(pr, defn, KFail, KSucceed)
    return trampoline(translate(pr, q, KFinalFail, KFinalSucceed),
                      ((vs,cs,()), ()))


# The parsing machine.
# continuation: trail -> result
# trail: () | ((vs,cs,ks), trail)
# vs: tuple of values from semantic actions
# cs: input character sequence (the current tail thereof)
# ks: () | ((fail_cont,success_cont), ks)

def trampoline(cont, trail):
    while cont is not None:
        cont, trail = cont(trail)
    return trail

def KFinalFail(trail):
    assert trail is ()
    return None, 'fail'
def KFinalSucceed(((vs,cs,ks), trail)):
    assert trail is ()
    assert ks is ()
    return None, (vs, cs)

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
def KFail(((vs,cs,((fk,_),ks)), trail)):
    return fk, trail
def KSucceed(((vs,cs,((_,sk),ks)), trail)):
    return sk, ((vs,cs,ks), trail)


# Smoke test

def Lit(c): return Item(lambda c1: c == c1)
def Or(q, r): return Cond(q, r, q)
# XXX is this really equivalent to a 'native' Or. As a tail call, too.
Succeed = Alter(lambda *vals: vals)

bit = Or(Lit('0'), Lit('1'))
twobits = Chain(bit, bit)

nbits_defs = {'nbits': Cond(bit, Succeed, Chain(bit, Ref('nbits')))}

def test(string):
#    return run(Lit('0'), (), string)
#    return run(bit, (), string)
#    return run(twobits, {}, (), string)
    return run(Ref('nbits'), nbits_defs, (), string)

## test('xy')
#. ((), 'xy')
## test('01101a')
#. (('0', '1', '1', '0', '1'), 'a')
