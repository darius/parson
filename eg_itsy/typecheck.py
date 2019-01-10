"""
Build a type environment and check against it.
Also, other semantic checks.
"""

from structs import Visitor
from ast import Void


def check(defs, complainer):
    sc = Scope(complainer=complainer)
    for d in defs:
        tc_def(d, sc)

def tc_opt_exp(opt_exp, te, type_):
    if opt_exp is not None:
        tc_exp(opt_exp, te, type_)

class Scope(object):

    def __init__(self, parent=None, complainer=None):
        self.parent = parent
        if complainer is None and parent is not None:
            complainer = parent.complainer
        self.complainer = complainer
        self.names = {}

    def def_var(self, name, type_, t):
        if name in self.names:
            self.err("Multiple definition", t)
        else:
            self.names[name] = (type_, t)   # or something

    def err(self, plaint, t):   # t = ast node
        self.complainer.semantic_error(plaint, where(t))

def where(t):
    if hasattr(t, 'pos'):
        return t.pos
    return where(getattr(t, t._meta_fields[0]))

void_type = Void(None)

class TCDef(Visitor):           # N.B. changing the term for top-level things to 'def'

    def Let(self, t, sc):    # sc = scope
        if t.opt_exp is not None and len(t.names) != 1:
            sc.err("Initializer doesn't match the number of variables", t)
        for name in t.names:
            sc.def_var(name, t.type, t)
        tc_opt_exp(t.opt_exp, sc, t.type)

    def Enum(self, t, sc):
        type_ = None    # Int()  # TODO or a new 'Enum_type' type?
        if t.opt_name is not None:
            sc.def_var(t.opt_name, type_, t)
            for name, opt_exp in t.pairs:
                sc.def_var(name, type_, t)
            for name, opt_exp in t.pairs:
                tc_opt_exp(opt_exp, sc, type_)

    # ... for the rest of this scaffold I'm not going to deal with sc yet XXX

    def To(self, t, sc):
        tc_type(t.signature, sc)
        subscope = Scope(sc)
        self(t.body, subscope)
        
    def Typedef(self, t, sc):
        tc_type(t.type, sc)

    def Record(self, t, sc):
        for type_, name in t.fields:
            tc_decl(type_, name, sc)

    def Block(self, t, sc):
        subscope = Scope(sc)
        for part in t.parts:
            self(part, subscope)

    def Exp(self, t, sc):
        tc_opt_exp(t.opt_exp, sc, void_type)

    def Return(self, t, sc):
        # XXX need to track if this is inside a function, and what the type is
        # (although the parser won't produce top-level Return, it's true)
        tc_opt_exp(t.opt_exp, sc, None)

    def Break(self, t, sc):
        # TODO check that we're in a loop
        pass

    def Continue(self, t, sc):
        # TODO check that we're in a loop
        pass

    def While(self, t, sc):
        tc_exp(t.exp, sc, None)
        self(t.block, sc)

    def Do(self, t, sc):
        self(t.block, sc)
        tc_exp(t.exp, sc, None)

    def If_stmt(self, t, sc):
        tc_exp(t.exp, sc, None)
        self(t.then_, sc)
        if t.opt_else:
            self(t.opt_else, sc)

    def For(self, t, sc):
        tc_opt_exp(t.opt_e1, sc, None)
        tc_opt_exp(t.opt_e2, sc, None)
        tc_opt_exp(t.opt_e3, sc, None)
        self(t.block, sc)

    def Switch(self, t, sc):
        tc_exp(t.exp, sc, None)
        for case in t.cases:
            self(case, sc)

    def Case(self, t, sc):
        for e in t.exps:
            tc_exp(e, sc, None)
        self(t.block, sc)

    def Default(self, t, sc):
        self(t.block, sc)

tc_def = TCDef()

class TCType(Visitor):
    pass

def tc_type(type_, sc):
    pass                        # XXX

def tc_decl(type_, name, sc):
    pass                        # XXX

class TCExp(Visitor):

    def Literal(self, t, sc, ctx):
        return None             # XXX

    def Variable(self, t, sc, ctx):
        return None                    # XXX

    def Address_of(self, t, sc, ctx):
        return self(t.e1, sc, None) # XXX

    def Sizeof_type(self, t, sc, ctx):
        tc_type(t.type, sc)     # XXX

    def Sizeof(self, t, sc, ctx):
        return self(t.e1, sc, None) # XXX

    def Deref(self, t, sc, ctx):
        return self(t.e1, sc, None) # XXX

    def Unary_exp(self, t, sc, ctx):
        return self(t.e1, sc, None) # XXX

    def Cast(self, t, sc, ctx):
        tc_type(t.type, sc)     # XXX
        return self(t.e1, sc, None) # XXX

    def Seq(self, t, sc, ctx):
        self(t.e1, sc, None) # XXX
        return self(t.e2, sc, None) # XXX

    def Pre_incr(self, t, sc, ctx):
        insist_lvalue(t.e1, sc)
        return self(t.e1, sc, None) # XXX

    def Post_incr(self, t, sc, ctx):
        insist_lvalue(t.e1, sc)
        return self(t.e1, sc, None) # XXX

    def If_exp(self, t, sc, ctx):
        self(t.e1, sc, None) # XXX
        self(t.e2, sc, None) # XXX
        self(t.e3, sc, None) # XXX

    def Assign(self, t, sc, ctx):
        insist_lvalue(t.e1, sc)
        self(t.e1, sc, None) # XXX
        return self(t.e2, sc, None) # XXX

    def Binary_exp(self, t, sc, ctx):
        self(t.e1, sc, None) # XXX
        self(t.e2, sc, None) # XXX

    def Index(self, t, sc, ctx):
        self(t.e1, sc, None) # XXX
        self(t.e2, sc, None) # XXX

    def Call(self, t, sc, ctx):
        self(t.e1, sc, None) # XXX
        for e in t.args:
            self(e, sc, None) # XXX

    def Dot(self, t, sc, ctx):
        self(t.e1, sc, None) # XXX

    def And(self, t, sc, ctx):
        self(t.e1, sc, None) # XXX
        self(t.e2, sc, None) # XXX

    def Or(self, t, sc, ctx):
        self(t.e1, sc, None) # XXX
        self(t.e2, sc, None) # XXX

    def Compound_exp(self, t, sc, ctx):
        for e in t.exps:
            self(e, sc, None) # XXX

tc_exp = TCExp()

def insist_lvalue(t, sc):
    if not is_lvalue(t, sc):
        sc.err("Not an lvalue", t)

# TODO check the C definition of lvalue
class IsLValue(Visitor):

    def Variable(self, t, sc):
        return True             # XXX need to check

    def Deref(self, t, sc):
        return True    # unless t.e1 is const...

    def Index(self, t, sc):
        return True    # unless t.e1 is const...

    def Dot(self, t, sc):
        return True    # unless t.e1 is const...

    def Pre_incr(self, t, sc):
        return False            # TODO maybe this could be true sometimes?

    def Post_incr(self, t, sc):
        return False            # TODO maybe this could be true sometimes?

    def If_exp(self, t, sc):
        return False   # Could be made to work, but it's not in C

    def default(self, t, sc):
        return False

is_lvalue = IsLValue()
