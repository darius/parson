"""
Abstract syntax of itsy.
"""

from structs import Struct


# Global declarations

class Global(    Struct('name opt_size opt_init')): pass
class Proc(      Struct('name params stmt')): pass


# Statements

class Auto(      Struct('decls')): pass
class Extern(    Struct('names')): pass
class Static(    Struct('names')): pass
class Block(     Struct('stmts')): pass
class If_stmt(   Struct('exp then_ opt_else')): pass
class While(     Struct('exp stmt')): pass
class Switch(    Struct('exp stmt')): pass
class Goto(      Struct('exp')): pass
class Return(    Struct('opt_exp')): pass
class Label(     Struct('name stmt')): pass
class Case(      Struct('literal stmt')): pass
class Exp(       Struct('opt_exp')): pass


# Expressions

class Assign(      Struct('e1 binop e2')): pass
class If_exp(      Struct('e1 e2 e3')): pass
class Binary_exp(  Struct('e1 binop e2')): pass
class Call(        Struct('e1 args')): pass
class Pre_incr(    Struct('op e1')): pass
class Post_incr(   Struct('e1 op')): pass
class Literal(     Struct('text kind')): pass  # TODO check octal constants for /[89]/
class Variable(    Struct('name')): pass
class Unary_exp(   Struct('unop e1')): pass

class Address_of(  Struct('e1')): pass    # TODO these are currently under Unary_exp instead

class And(         Struct('e1 e2')): pass   # TODO maybe use instead of Binary_exp
class Or(          Struct('e1 e2')): pass

def Index(e1, e2):
    return Unary_exp('*', Binary_exp(e1, '+', e2))
