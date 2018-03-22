"""
Build a type environment and check against it.
TODO fill out and use
"""

from structs import Visitor

def opt_exp_typecheck(opt_exp, te, type_):
    if opt_exp is not None:
        tc_exp(opt_exp, te, type_)

class TypeEnv(object):
    def extend(self, name, type_):
        pass                    # XXX

class TCDef(Visitor):           # N.B. changing the term for top-level things to 'def'

    def Let(self, t, te):    # te = type environment
        for name in t.names:
            te.extend(name, t.type)
        opt_exp_typecheck(t.opt_exp, te, t.type)

    def Enum(self, t, te):
        type_ = Int()  # TODO or a new 'Enum_type' type?
        if t.opt_name is not None:
            te.extend(t.opt_name, type_)
            for name, opt_exp in t.pairs:
                te.extend(name, type_)
            for name, opt_exp in t.pairs:
                opt_exp_typecheck(opt_exp, te, type_)

    # ...

tc_def = TCDef()
