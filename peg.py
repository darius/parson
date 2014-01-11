"""
A PEG matcher using explicit control instead of recursion.
Avoids Python stack overflow.
Also a step towards compiling instead of interpreting.

to do: optimize q==y with Nip
to do: produce code instead of closures
to do: bounce less often

=
+
"""

def Drop(cont): return lambda (_, trail): (cont, trail)
def Nip(cont): return lambda (entry, (_, trail)): (cont, (entry, trail))
def Dup(cont): return lambda (entry, trail): (cont, (entry, (entry, trail)))

def Alter(fn):     return lambda pr, f, s: lambda ((vs,cs,ks), trail): (
    s, ((fn(*vs),cs,ks), trail))
def Item(ok):      return lambda pr, f, s: lambda ((vs,cs,ks), trail): (
    (s, ((vs+(cs[0],), cs[1:], ks), trail)) if cs and ok(cs[0])
    else (f, trail))
def Ref(name):     return lambda pr, f, s: lambda ((vs,cs,ks), trail): (
    pr[name], ((vs,cs,((f,s),ks)), trail))

def Fail(pr, f, s): return Drop(f)
def Chain(q, r):   return lambda pr, f, s: q(pr, f, r(pr, f, s))
def Cond(q, n, y): return lambda pr, f, s: Dup(q(pr, n(pr, f, s), Drop(y(pr, f, s))))

def trampoline(cont, trail):
    while cont is not None:
        cont, trail = cont(trail)
    return trail

def run(q, defns, vs, cs):
    def fail(trail):
        assert trail is ()
        return None, 'fail'
    def succeed(((vs,cs,ks), trail)):
        assert trail is ()
        assert ks is ()
        return None, (vs, cs)
    pr = {}
    for name, defn in defns.items():
        pr[name] = defn(pr, fnfail, fnsucceed)
    return trampoline(q(pr, fail, succeed),
                      ((vs,cs,()), ()))

def fnsucceed(((vs,cs,((_,sk),ks)), trail)):
    return sk, ((vs,cs,ks), trail)
def fnfail(((vs,cs,((fk,_),ks)), trail)):
    return fk, trail


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
