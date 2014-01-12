"""
A PEG matcher using explicit control instead of recursion.
Avoids Python stack overflow.
Also a step towards compiling instead of interpreting.

to do: test this: optimize q==y with Nip
to do: produce code instead of closures
to do: bounce less often

=
+
"""

def Drop(cont): return lambda (_, trail): (cont, trail)
def Nip(cont): return lambda (entry, (_, trail)): (cont, (entry, trail))
def Dup(cont): return lambda (entry, trail): (cont, (entry, (entry, trail)))

def fnsucceed(((vs,cs,((_,sk),ks)), trail)):
    return sk, ((vs,cs,ks), trail)
def fnfail(((vs,cs,((fk,_),ks)), trail)):
    return fk, trail

def finalfail(trail):
    assert trail is ()
    return None, 'fail'
def finalsucceed(((vs,cs,ks), trail)):
    assert trail is ()
    assert ks is ()
    return None, (vs, cs)

Fail = 'fail', None
def Alter(fn):     return 'alter', fn
def Item(ok):      return 'item', ok
def Ref(name):     return 'ref', name
def Chain(q, r):   return 'chain', (q, r)
def Cond(q, n, y): return 'cond', (q, n, y)

def translate(pr, peg, f, s):
    tag, arg = peg
    if tag == 'fail':
        return Drop(f) 
    elif tag == 'alter':
        fn = arg
        return lambda ((vs,cs,ks), trail): (s, ((fn(*vs),cs,ks), trail))
    elif tag == 'item':
        ok = arg
        return lambda ((vs,cs,ks), trail): (
            (s, ((vs+(cs[0],), cs[1:], ks), trail)) if cs and ok(cs[0])
            else (f, trail))
    elif tag == 'ref':
        name = arg
        return lambda ((vs,cs,ks), trail): (
            pr[name], ((vs,cs,((f,s),ks)), trail))
    elif tag == 'chain':
        return translate(pr, arg[0], f,
                         translate(pr, arg[1], f, s))
    elif tag == 'cond':
        q, n, y = arg
        if q == y:
            yy = Nip(s)
        elif y[0] == 'chain' and y[1][0] == q:
            yy = Nip(translate(pr, y[1][1], f, s))
        else:
            yy = Drop(translate(pr, y, f, s))
        return Dup(translate(pr, q, translate(pr, n, f, s), yy))
    else:
        assert False

def trampoline(cont, trail):
    while cont is not None:
        cont, trail = cont(trail)
    return trail

def run(q, defns, vs, cs):
    pr = {}
    for name, defn in defns.items():
        pr[name] = translate(pr, defn, fnfail, fnsucceed)
    return trampoline(translate(pr, q, finalfail, finalsucceed),
                      ((vs,cs,()), ()))


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
