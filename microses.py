"""
Abstract syntax for MicroSES.
"""

from structs import Struct as S

class Data(S('string')):
    pass

class Array(S('args')):
    pass

class Object(S('props')):
    pass

class Variable(S('name')):
    pass

class ExprHole(S('')):
    pass

class MatchData(S('string')):
    pass

class MatchArray(S('params')):
    pass

class MatchObject(S('prop_params')):
    pass

class MatchVariable(S('name')):
    pass

class PatternHole(S('')):
    pass

class Spread(S('expr')):
    pass

class Rest(S('pattern')):
    pass

class Optional(S('name expr')):
    pass

class SpreadObj(S('expr')):
    pass

class Prop(S('key expr_opt')):
    pass

class RestObj(S('pattern')):
    pass

class MatchProp(S('key pattern')):
    pass

class OptionalProp(S('name expr')):
    pass

class Computed(S('expr')):
    pass

class Quasi(S('string')):
    pass

def QUnpack():
    pass

class Get(S('primary name')):
    pass

class Index(S('primary expr')):
    pass

class Call(S('primary args')):
    pass

class Tag(S('primary quasi')):
    pass

class GetLater(S('primary name')):
    pass

class IndexLater(S('primary expr')):
    pass

class CallLater(S('primary args')):
    pass

class TagLater(S('primary quasi')):
    pass

class Delete(S('field_expr')):
    pass

class UnaryOp(S('op expr')):
    pass

class BinaryOp(S('expr1 op expr2')):
    pass

class AndThen(S('expr1 expr2')):
    pass

class OrElse(S('expr1 expr2')):
    pass

class Assign(S('lvalue op expr')):
    pass

class Arrow(S('params block')):
    pass

class Lambda(S('params expr')):
    pass

class If(S('test then else_opt')):
    pass

class For(S('decls test_opt update_opt block')):
    pass

class ForOf(S('decl_op binding expr block')):
    pass

class Decl(S('decl_op bindings')):
    pass

class While(S('expr block')):
    pass

class Try(S('block catcher_opt finalizer_opt')):
    pass

class Switch(S('expr branches')):
    pass

class Debugger(S('')):
    pass

class Return(S('expr_opt')):
    pass

class Break(S('')):
    pass

class Throw(S('expr')):
    pass

class Branch(S('labels body terminator')):
    pass

class Case(S('expr')):
    pass

class Default(S('')):
    pass

class Block(S('body')):
    pass
