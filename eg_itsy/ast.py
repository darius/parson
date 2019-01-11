"""
Abstract syntax of itsy.
"""

from structs import Struct


# Declarations

class To(        Struct('pos name signature body')): pass
class Typedef(   Struct('pos name type')): pass
class Let(       Struct('pos names type opt_exp')): pass
class Enum(      Struct('pos opt_name pairs')): pass
class Record(    Struct('pos kind opt_name fields')): pass # kind = 'struct' or 'union'


# Statements

class Block(     Struct('pos parts')): pass

class Exp(       Struct('pos opt_exp')): pass
class Return(    Struct('pos opt_exp')): pass
class Break(     Struct('pos ')): pass
class Continue(  Struct('pos ')): pass
class While(     Struct('pos exp block')): pass
class Do(        Struct('pos block exp')): pass
class For(       Struct('pos opt_e1 opt_e2 opt_e3 block')): pass
class If_stmt(   Struct('pos exp then_ opt_else')): pass
class Switch(    Struct('pos exp cases')): pass

class Case(      Struct('pos exps block')): pass
class Default(   Struct('pos block')): pass


# Types

class Type_name( Struct('pos name')): pass
class Pointer(   Struct('pos type')): pass
class Array(     Struct('pos size type')): pass
class Signature( Struct('pos params return_type')): pass  # params are (type, (name or '')) pairs

# TODO rename fields like 'type' to 'base_type' or something

class Int_type(  Struct('size signedness')): pass
class Float_type(Struct('size')): pass

def Void(pos): return Type_name(pos, 'void')  # for now, anyway

def spread_params(names, type_):
    return tuple((type_, name) for name in names)

def chain(*seqs):
    return sum(seqs, ())


# Expressions

class Seq(         Struct('e1 e2')): pass
class Assign(      Struct('e1 opt_binop e2')): pass
class If_exp(      Struct('e1 e2 e3')): pass
class And(         Struct('e1 e2')): pass
class Or(          Struct('e1 e2')): pass
class Binary_exp(  Struct('e1 binop e2')): pass
class Index(       Struct('e1 e2')): pass
class Call(        Struct('e1 args')): pass
class Dot(         Struct('e1 field')): pass
class Deref(       Struct('e1')): pass
class Post_incr(   Struct('e1 op')): pass
class Cast(        Struct('e1 type')): pass

class Literal(     Struct('pos text kind')): pass
class Variable(    Struct('pos name')): pass
class Address_of(  Struct('pos e1')): pass
class Sizeof_type( Struct('pos type')): pass
class Sizeof(      Struct('pos e1')): pass
class Unary_exp(   Struct('pos unop e1')): pass
class Pre_incr(    Struct('pos e1 op')): pass
class Compound_exp(Struct('pos exps')): pass
