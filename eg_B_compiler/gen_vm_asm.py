"""
Compile from AST to assembly for a stack machine.
"""

from itertools import count
from structs import Visitor

def gen_program(global_decls):
    for gd in global_decls:
        gen_global_decl(gd)
        print

def asm(instruction='', arguments=(), label='', comment=None):
    assert instruction or not arguments
    fields = [label, instruction, ', '.join(arguments)]
    if comment: fields += ['# ' + comment]
    print '\t'.join(fields).rstrip()

# Generated labels need to be distinct from B identifiers. We make
# sure of this with '.'.
def Label(stem):
    return '%s.%d' % (stem, next(label_counter))

label_counter = count()


class GenGlobalDecl(Visitor):

    def Global(self, t):
        args = []
        if t.opt_size is not None:
            args.append('size(%s)' % gen_literal(t.opt_size))
        if t.opt_init is not None:
            args.append('init(%s)' % ', '.join(map(gen_literal, t.opt_init)))
        asm('global', args, label=t.name)

    def Proc(self, t):
        asm('proc', label=t.name)
        asm('params', t.params)
        gen_stmt(t.stmt)
        asm('return_void') # TODO skip if redundant
        asm('endproc')  # Telling the assembler it can discard local labels

gen_global_decl = GenGlobalDecl()


class GenStmt(Visitor):

    def Auto(self, t):
        for (name, XXX) in t.decls:
            args = [] if XXX is None else [repr(XXX)]  # TODO fill in
            asm('local', args, label=name)

    def Extern(self, t):
        for name in t.names:
            asm('extern', label=name)

    def Static(self, t):
        for name in t.names:
            asm('static', label=name)

    def Block(self, t):
        for stmt in t.stmts:
            gen_stmt(stmt)

    def If_stmt(self, t):
        if_not = Label('endif' if t.opt_else is None else 'else')
        gen_exp(t.exp)
        asm('if_not', [if_not])
        gen_stmt(t.then_)
        if t.opt_else is None:
            asm(label=if_not)
        else:
            endif = Label('endif')
            asm('jump', [endif])
            asm(label=if_not)
            gen_stmt(t.opt_else)
            asm(label=endif)

    def While(self, t):
        enter = Label('while')
        loop = Label('loop')
        asm('jump', [enter])
        asm(label=loop)
        gen_stmt(t.stmt)
        asm(label=enter)
        gen_exp(t.exp)
        asm('if', [loop])

    def Switch(self, t):
        gen_exp(t.exp)
        asm('switch')
        labeler = LabelCases()
        labeler(t.stmt)
        for literal, label in labeler.cases:
            asm('case', [gen_literal(literal), label])
        asm('endcases')
        gen_stmt(t.stmt)

    def Goto(self, t):
        # TODO optimize for constant t.exp, defined by a B label
        gen_exp(t.exp)
        asm('goto')

    def Return(self, t):
        if t.opt_exp is None:
            asm('return_void')
        else:
            gen_exp(t.opt_exp)
            asm('return')

    def Label(self, t):
        asm(label=t.name)    # TODO relate this to Goto's at compile time
        gen_stmt(t.stmt)

    def Case(self, t):
        asm(label=t.case_label, comment=gen_literal(t.literal))
        gen_stmt(t.stmt)

    def Exp(self, t):
        if t.opt_exp is not None:
            gen_exp(t.opt_exp)
            asm('pop')

gen_stmt = GenStmt()


def gen_literal(literal):
    return literal.text


class LabelCases(Visitor):
    def __init__(self):
        self.cases = []

    def Case(self, t):
        assert not hasattr(t, 'case_label')
        t.case_label = Label('case')
        self.cases.append((t.literal, t.case_label))
        self(t.stmt)

    def Switch(self, t):
        pass

    def Block(self, t):
        for stmt in t.stmts:
            self(stmt)
    def If_stmt(self, t):
        self(t.then_)
        if t.opt_else is not None:
            self(t.opt_else)
    def While(self, t):
        self(t.stmt)
    def Label(self, t):
        self(t.stmt)

    def default(self, t):
        pass


class GenExp(Visitor):

    def Assign(self, t):
        gen_lvalue(t.e1)
        gen_exp(t.e2)
        asm('assign', [t.binop])
    
    def If_exp(self, t):
        else_, endif = Label('else'), Label('endif')
        gen_exp(t.e1)
        asm('if_not', [else_])
        gen_exp(t.e2)
        asm('jump', [endif])
        asm(label=else_)
        gen_exp(t.e3)
        asm(label=endif)
    
    def Binary_exp(self, t):
        gen_exp(t.e1)
        gen_exp(t.e2)
        asm('op2', [t.binop])
    
    def Call(self, t):
        gen_exp(t.e1)
        for arg in t.args:
            gen_exp(arg)
        asm('call', [str(len(t.args))])
    
    def Pre_incr(self, t):
        gen_lvalue(t.e1)
        asm('preinc', [t.op])
    
    def Post_incr(self, t):
        gen_lvalue(t.e1)
        asm('postinc', [t.op])
    
    def Literal(self, t):
        asm('push', [gen_literal(t)])
    
    def Variable(self, t):
        asm('value', [t.name])
    
    def Unary_exp(self, t):
        gen_exp(t.e1)
        asm('op1', [t.unop])
    
    def Address_of(self, t):
        gen_lvalue(t.e1)
    
    def And(self, t):
        if_not = Label('and')
        gen_exp(t.e1)
        asm('if_pop_else_skip', [if_not])
        gen_exp(t.e2)
        asm(label=if_not)
    
    def Or(self, t):
        if_so = Label('or')
        gen_exp(t.e1)
        asm('if_skip_else_pop', [if_so])
        gen_exp(t.e2)
        asm(label=if_so)

gen_exp = GenExp()


class GenLvalue(Visitor):
    
    def Variable(self, t):
        asm('addr', [t.name])
    
    def Unary_exp(self, t):
        if t.unop != '*':
            raise Exception("Not an lvalue", t)
        gen_exp(t.e1)

    def default(self, t):
        raise Exception("Not an lvalue", t)

gen_lvalue = GenLvalue()
