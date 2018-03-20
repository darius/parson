"""
Abstract syntax of itsy.
"""

from structs import Struct

def TBD(*args):
    raise Exception("Not supported yet: %r" % args)


# Declarations

class To(        Struct('name signature body')): pass
class Let(       Struct('names type opt_exp')): pass
class Enum(      Struct('opt_name pairs')): pass


# Statements

class Block(     Struct('parts')): pass

class Exp(       Struct('opt_exp')): pass
class Return(    Struct('opt_exp')): pass
class Break(     Struct('')): pass
class Continue(  Struct('')): pass
class While(     Struct('exp block')): pass
class Do(        Struct('block exp')): pass
class Ifs(       Struct('parts')): pass
class For(       Struct('opt_e1 opt_e2 opt_e3 block')): pass
class Switch(    Struct('exp cases')): pass

class Case(      Struct('exps block')): pass
class Default(   Struct('block')): pass


# Types

class Type_name( Struct('name')): pass
class Pointer(   Struct('type')): pass
class Array(     Struct('size type')): pass
class Signature( Struct('params return_type')): pass  # params are (type, (name or '')) pairs

# TODO rename fields like 'type' to 'base_type' or something

def Void(): return Type_name('void')  # for now, anyway

def spread_params(names, type_):
    return tuple((type_, name) for name in names)

def chain(*seqs):
    return sum(seqs, ())


# Expressions

def Ifs_exp(e1, e2, e3, *es):
    return If_exp(e1, e2, e3 if not es else Ifs_exp(e3, *es))

class Literal(     Struct('value')): pass
class String(      Struct('value')): pass
class Char_literal(Struct('value')): pass
class Variable(    Struct('name')): pass
class Address_of(  Struct('e1')): pass
class Sizeof_type( Struct('type')): pass
class Sizeof(      Struct('e1')): pass
class Deref(       Struct('e1')): pass
class Unary_exp(   Struct('unop e1')): pass
class Cast(        Struct('e1 type')): pass
class Seq(         Struct('e1 e2')): pass
class Pre_incr(    Struct('e1')): pass
class Pre_decr(    Struct('e1')): pass
class Post_incr(   Struct('e1')): pass
class Post_decr(   Struct('e1')): pass
class If_exp(      Struct('e1 e2 e3')): pass
class Assign(      Struct('e1 opt_binop e2')): pass
class Binary_exp(  Struct('e1 binop e2')): pass
class Index(       Struct('e1 e2')): pass
class Call(        Struct('e1 args')): pass
class Dot(         Struct('e1 field')): pass
class And(         Struct('e1 e2')): pass
class Or(          Struct('e1 e2')): pass
class Compound_exp(Struct('exps')): pass
