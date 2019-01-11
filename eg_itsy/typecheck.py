"""
Build a type environment and check against it.
Also, other semantic checks.
"""

# Glossary:
#  t: ast node
#  sc: scope
#  def: a top-level or block-level definition

from structs import Struct, Visitor
from ast import Void


# TODO rename to 'analyze'

def check(defs, prims, complainer): # TODO use prims
    sc = Scope(complainer=complainer)
    sc.names.update(prims)
    for d in defs:
        enter_def(d, sc)
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

    def define(self, name, meaning):
        if name in self.names:
            self.err("Multiple definition", meaning.t) # TODO also point to first def
        else:
            self.names[name] = meaning

    def err(self, plaint, t):
        self.complainer.semantic_error(plaint, where(t))

def where(t):
    if hasattr(t, 'pos'):
        return t.pos
    return where(getattr(t, t._meta_fields[0]))

class LetMeaning      (Struct('t type')): pass
class ToMeaning       (Struct('t')): pass
class EnumTypeMeaning (Struct('t')): pass
class EnumConstMeaning(Struct('t')): pass
class TypedefMeaning  (Struct('t')): pass
class RecordMeaning   (Struct('t')): pass

# First, shallowly analyze scope

def enter_block(block, sc):
    for d in block.parts:
        enter_part(d, sc)

class EnterDef(Visitor):

    def Let(self, t, sc):
        for name in t.names:
            sc.define(name, LetMeaning(t, t.type))

    def Enum(self, t, sc):
        if t.opt_name is not None:
            sc.define(t.opt_name, EnumTypeMeaning(t))
            for name, opt_exp in t.pairs:
                sc.define(name, EnumConstMeaning(t))

    def To(self, t, sc):
        sc.define(t.name, ToMeaning(t))
        
    def Typedef(self, t, sc):
        sc.define(t.name, TypedefMeaning(t))

    def Record(self, t, sc):
        if t.opt_name:
            sc.define(t.opt_name, RecordMeaning(t))
        # TODO check that the same field isn't multiply-defined

    def default(self, t, sc):
        # TODO Probably the parser doesn't give us any of these, so this is probably unneeded:
        sc.err("Not allowed at top level", t)

enter_def = EnterDef()

# A 'part' is a block element.
class EnterPart(Visitor):

    def Let(self, t, sc):
        enter_def(t, sc)

    def Enum(self, t, sc):
        enter_def(t, sc)

    def To(self, t, sc):
        sc.err("Nested function definition", t)
        
    def Typedef(self, t, sc):
        enter_def(t, sc)

    def Record(self, t, sc):
        enter_def(t, sc)

    def default(self, t, sc):
        pass

enter_part = EnterPart()


# Now check the types and recur
# TODO also check that locals are not used before their def

void_type = Void(None)

class TCDef(Visitor):

    def Let(self, t, sc):
        if t.opt_exp is not None and len(t.names) != 1:
            sc.err("Initializer doesn't match the number of variables", t)
        tc_opt_exp(t.opt_exp, sc, t.type)

    def Enum(self, t, sc):
        type_ = None    # Int()  # TODO or a new 'Enum_type' type?
        if t.opt_name is not None:
            for name, opt_exp in t.pairs:
                tc_opt_exp(opt_exp, sc, type_)

    def To(self, t, sc):
        tc_type(t.signature, sc)
        subscope = Scope(sc)
        # XXX: enter the param names first
        self(t.body, subscope)
        
    def Typedef(self, t, sc):
        tc_type(t.type, sc)

    def Record(self, t, sc):
        for type_, name in t.fields:
            tc_decl(type_, name, sc)

    def Block(self, t, sc):
        subscope = Scope(sc)
        enter_block(t, subscope)
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
