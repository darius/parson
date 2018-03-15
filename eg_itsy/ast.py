"""
Abstract syntax of itsy.
Emit C code.
"""

from structs import Struct


def TBD(*args):
    raise Exception("Not supported yet: %r" % args)

def indent(s):
    return s.replace('\n', '\n  ')

def embrace(lines):
    return '{\n  %s\n}' % indent('\n'.join(lines))

def opt_c(opt_x, if_none, if_some):
    return if_none if opt_x is None else if_some % opt_x.c()


# Declarations

class Let(Struct('names type opt_exp')):
    def c(self):
        if self.opt_exp is not None and len(self.names) != 1:
            raise Exception("XXX yadda yadda")
        assign = opt_c(self.opt_exp, '', ' = %s')
        return '\n'.join('%s%s;' % (self.type.c_decl(name), assign)
                         for name in self.names)

class Array_decl(Struct('name type exps')):
    def c(self):
        inits = [e.c() for e in self.exps]
        return '%s = %s;' % (self.type.c_decl(self.name), embrace(inits))

class Enum(Struct('opt_name pairs')):
    def c(self):
        # XXX is this right when we mix explicit and implicit values?
        enums = ['%s%s,' % (name, opt_c(opt_exp, '', ' = %s'))
                 for name, opt_exp in self.pairs]
        return 'enum %s%s' % (self.opt_name + ' ' if self.opt_name else '',
                              embrace(enums))

class To(Struct('name params opt_return_type body')):
    def c(self):
        return_type = opt_c(self.opt_return_type, 'void', '%s')
        params_c = ', '.join(type_.c_decl(name)
                             for names, type_ in self.params
                             for name in names)
        return '%s %s(%s) %s' % (return_type,
                                 self.name,
                                 params_c or 'void',
                                 self.body.c())


# Types

class Type(object):
    def c_decl(self, name):
        return '%s %s' % self.decl(name)
    def decl(self, e):
        return self.c(), e

class Int(Struct('', supertype=(Type,))):          # TODO size, signedness
    def c(self):
        return 'int'

class Char(Struct('', supertype=(Type,))):          # TODO signedness
    def c(self):
        return 'char'

class Void(Struct('', supertype=(Type,))):
    def c(self):
        return 'void'

class Float(Struct('name', supertype=(Type,))):
    def c(self):
        return self.name

class Type_name(Struct('name', supertype=(Type,))):
    def c(self):
        return self.name

class Pointer(Struct('type', supertype=(Type,))):
    def c(self):
        return '*%s' % self.type.c() # XXX right?
    def decl(self, e):
        return self.type.decl('(*%s)' % e)

class Array(Struct('type size', supertype=(Type,))):
    def c(self):
        return '%s[%s]' % (self.type.c(), self.size.c())
    def decl(self, e):
        a, b = self.type.decl(e)
        return a, '%s[%s]' % (b, self.size.c())

class Function(Struct('param_types return_type', supertype=(Type,))):
    def c(self):
        return '(%s)(%s)' % (self.return_type.c(), self.params_c())
    def params_c(self):
        return ', '.join(t.c() for t in self.param_types)
    def decl(self, e):
        return self.type.decl('*%s(%s)' % (e, self.params_c()))


# Statements

class Exp(Struct('opt_exp')):
    def c(self):
        return opt_c(self.opt_exp, ';', '%s;')

class Return(Struct('opt_exp')):
    def c(self):
        return opt_c(self.opt_exp, 'return;', 'return %s;')

class Break(Struct('')):
    def c(self):
        return 'break;'

class Continue(Struct('')):
    def c(self):
        return 'continue;'

class While(Struct('exp block')):
    def c(self):
        return 'while (%s) %s' % (self.exp.c(), self.block.c())

class Do(Struct('block exp')):
    def c(self):
        return 'do %s while(%s)' % (self.block.c(), self.exp.c())

class Ifs(Struct('parts')):
    def c(self):
        clauses = zip(self.parts[0:-1:2], self.parts[1::2])
        else_block = self.parts[-1]
        ifs = ' else '.join('if (%s) %s' % (exp.c(), block.c())
                            for exp, block in clauses)
        return ifs + opt_c(else_block, '', ' else %s')

class For(Struct('opt_e1 opt_e2 opt_e3 block')):
    def c(self):
        e1 = opt_c(self.opt_e1, '', '%s')
        e2 = opt_c(self.opt_e2, '', '%s')
        e3 = opt_c(self.opt_e3, '', '%s')
        return 'for (%s; %s; %s) %s' % (e1, e2, e3, self.block.c())

class Switch(Struct('exp cases')):
    def c(self):
        cases = [case_.c() for case_ in self.cases]
        return 'switch (%s) %s' % (self.exp.c(), embrace(cases))

class Case(Struct('exps block')):
    def c(self):
        cases = '\n'.join('case %s:' % e.c() for e in self.exps)
        return '%s %s\nbreak;' % (cases, self.block.c())

class Default(Struct('block')):
    def c(self):
        return 'default: %s\nbreak;' % self.block.c()

class Block(Struct('decls stmts')):
    def c(self):
        return embrace(x.c() for x in self.decls + self.stmts)


# Expressions

class Literal(Struct('value')):
    def c(self):
        return repr(self.value)

class String(Struct('value')):
    def c(self):
        return '"%s"' % self.value       # XXX escaping as C

class Char_literal(Struct('value')):
    def c(self):
        return "'%s'" % self.value    # XXX escaping

class Variable(Struct('name')):
    def c(self):
        return self.name

class Address_of(Struct('exp')):
    def c(self):
        return '(&%s)' % self.exp.c()

class Sizeof_type(Struct('type')):
    def c(self):
        return 'sizeof(%s)' % self.type.c()

class Sizeof(Struct('exp')):
    def c(self):
        return '(sizeof %s)' % self.exp.c()

class Deref(Struct('exp')):
    def c(self):
        return '(*%s)' % self.exp.c()

class Cast(Struct('type exp')):
    def c(self):
        return '((%s) %s)' % (self.type.c(), self.exp.c())

class Seq(Struct('e1 e2')):
    def c(self):
        return '(%s, %s)' % (self.e1.c(), self.e2.c())

class Pre_incr(Struct('exp')):
    def c(self):
        return '(++%s)' % self.exp.c()

class Pre_decr(Struct('exp')):
    def c(self):
        return '(--%s)' % self.exp.c()

class Post_incr(Struct('exp')):
    def c(self):
        return '(%s++)' % self.exp.c()

class Post_decr(Struct('exp')):
    def c(self):
        return '(%s--)' % self.exp.c()

def Ifs_exp(e1, e2, e3, *es):
    return If_exp(e1, e2, e3 if not es else Ifs_exp(e3, *es))

class If_exp(Struct('e1 e2 e3')):
    def c(self):
        return '(%s ? %s : %s)' % (self.e1.c(), self.e2.c(), self.e3.c())

class Assign(Struct('e1 opt_binop e2')):
    def c(self):
        op = self.opt_binop or ''
        return '(%s %s= %s)' % (self.e1.c(), op, self.e2.c())

class Binary_exp(Struct('e1 binop e2')):
    def c(self):
        return '(%s %s %s)' % (self.e1.c(), self.binop, self.e2.c())

class Unary_exp(Struct('unop e1')):
    def c(self):
        return '(%s%s)' % (self.unop, self.e1.c())

class Index(Struct('e1 e2')):
    def c(self):
        return '%s[%s]' % (self.e1.c(), self.e2.c())

class Call(Struct('e1 args')):
    def c(self):
        # TODO: beware of precedence problems from assuming ', ' precedence
        return '%s(%s)' % (self.e1.c(), ', '.join(e.c() for e in self.args))

class Dot(Struct('e1 field')):
    def c(self):
        if isinstance(self.e1, Deref):
            return '%s->%s' % (self.e1.exp.c(), self.field)
        else:
            return '%s.%s' % (self.e1.c(), self.field)

class And(Struct('e1 e2')):
    def c(self):
        return '(%s && %s)' % (self.e1.c(), self.e2.c())

class Or(Struct('e1 e2')):
    def c(self):
        return '(%s || %s)' % (self.e1.c(), self.e2.c())
