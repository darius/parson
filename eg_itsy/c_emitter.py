"""
Emit C code from an AST.
"""

from structs import Visitor
import ast

def indent(s):
    return s.replace('\n', '\n    ')

def embrace(lines):
    return '{\n    %s\n}' % indent('\n'.join(lines))

def opt_c_exp(opt_e, if_some='', p=0):
    return '' if opt_e is None else if_some + c_exp(opt_e, p)

def opt_space(opt_s):
    return ' %s' % opt_s if opt_s else ''


# Declarations and statements (either can appear in a block)
# TODO rename 'declaration' to avoid confusion with c_decl below

class CEmitter(Visitor):

    def To(self, t):
        return '%s %s' % (c_decl(t.signature, t.name), c(t.body))

    def Typedef(self, t):
        return 'typedef %s;' % c_decl(t.type, t.name)

    def Let(self, t):
        if t.opt_exp is not None and len(t.names) != 1:
            raise Exception("XXX yadda yadda")
        assign = opt_c_exp(t.opt_exp, ' = ', elem_prec)
        return '\n'.join('%s%s;' % (c_decl(t.type, name), assign)
                         for name in t.names)

    def Enum(self, t):
        enums = ['%s%s,' % (name, opt_c_exp(opt_exp, ' = '))
                 for name, opt_exp in t.pairs]
        return 'enum%s %s;' % (opt_space(t.opt_name), embrace(enums))

    def Record(self, t):
        lines = []
        if t.opt_name:
            lines.append('typedef struct %s %s;' % (t.opt_name, t.opt_name))
        c_defn = '%s%s %s' % (t.kind,
                              opt_space(t.opt_name),
                              embrace(c_decl(type_, name) + ';'
                                      for type_, name in t.fields))
        lines.append(c_defn)
        return '\n'.join(lines)

    def Block(self, t):
        return embrace(map(c, t.parts));

    def Exp(self, t):
        return opt_c_exp(t.opt_exp) + ';'

    def Return(self, t):
        return 'return%s;' % opt_c_exp(t.opt_exp, ' ')

    def Break(self, t):
        return 'break;'

    def Continue(self, t):
        return 'continue;'

    def While(self, t):
        return 'while (%s) %s' % (c_exp(t.exp), c(t.block))

    def Do(self, t):
        return 'do %s while(%s)' % (c(t.block), c_exp(t.exp))

    def Ifs(self, t):
        clauses = zip(t.parts[0:-1:2], t.parts[1::2])
        else_block = t.parts[-1]
        branches = ['if (%s) %s' % (c_exp(exp), c(block))
                    for exp, block in clauses]
        if else_block: branches.append(c(else_block))
        return ' else '.join(branches)

    def For(self, t):
        return 'for (%s; %s; %s) %s' % (opt_c_exp(t.opt_e1),
                                        opt_c_exp(t.opt_e2),
                                        opt_c_exp(t.opt_e3),
                                        c(t.block))

    def Switch(self, t):
        return 'switch (%s) %s' % (c_exp(t.exp),
                                   embrace(map(c, t.cases)))

    def Case(self, t):
        cases = '\n'.join('case %s:' % c_exp(e) for e in t.exps)
        return '%s %s break;' % (cases, c(t.block))

    def Default(self, t):
        return 'default: %s break;' % c(t.block)

c = c_emit = CEmitter()


# Types

def c_type(type_):
    return c_decl(type_, '')

def c_decl(type_, name):
    return ('%s %s' % decl_pair(type_, name, 0)).rstrip()

class DeclPair(Visitor):

    def Type_name(self, t, e, p): # e: expression-like C fragment, p: surrounding precedence
        return t.name, e

    def Pointer(self, t, e, p):
        return self(t.type,
                    '*%s' % hug(e, p, 2),
                    2)

    def Array(self, t, e, p):
        return self(t.type,
                    '%s[%s]' % (hug(e, p, 1), opt_c_exp(t.size)),
                    1)

    def Signature(self, t, e, p):
        c_params = ', '.join(c_decl(type_, name) for type_, name in t.params)
        return self(t.return_type,
                    '%s(%s)' % (hug(e, p, 1), c_params or 'void'),
                    1)

decl_pair = DeclPair()

def hug(s, outer, inner):
    return s if outer <= inner else '(%s)' % s # XXX is '<=' quite right? instead of '<'?


# Expressions

def c_exp(e, p=0):              # p: surrounding precedence
    return c_exp_emitter(e, p)

class CExpEmitter(Visitor):

    def Literal(self, t, p):
        return t.text

    def Variable(self, t, p):
        return t.name

    def Address_of(self, t, p):
        return fmt1(p, unary_prec, '&%s', t.e1)

    def Sizeof_type(self, t, p):
        return 'sizeof(%s)' % c_type(t.type)

    def Sizeof(self, t, p):
        return fmt1(p, unary_prec, 'sizeof %s', t.e1)

    def Deref(self, t, p):
        return fmt1(p, unary_prec, '*%s', t.e1)

    def Unary_exp(self, t, p):
        return fmt1(p, unary_prec, t.unop + '%s', t.e1)

    def Cast(self, t, p):
        return wrap(cast_prec, p, '(%s) %s' % (c_type(t.type),
                                               self(t.e1, cast_prec)))

    def Seq(self, t, p):
        return fmt2(p, ',', t.e1, t.e2, fmt_str = '%s%s %s')

    def Pre_incr(self, t, p):
        return fmt1(p, unary_prec, '++%s', t.e1)

    def Pre_decr(self, t, p):
        return fmt1(p, unary_prec, '--%s', t.e1)

    def Post_incr(self, t, p):
        return fmt1(p, postfix_prec, '%s++', t.e1)

    def Post_decr(self, t, p):
        return fmt1(p, postfix_prec, '%s--', t.e1)

    def If_exp(self, t, p):
        lp, rp = binaries['?:']
        return wrap(rp, p, # TODO recheck that rp is the right thing here in place of the usual lp
                    '%s ? %s : %s' % (self(t.e1, lp),
                                      self(t.e2, 0),
                                      self(t.e3, rp)))

    def Assign(self, t, p):
        return fmt2(p, (t.opt_binop or '') + '=', t.e1, t.e2) # TODO clumsy

    def Binary_exp(self, t, p):
        op = '^' if t.binop == '@' else t.binop
        return fmt2(p, op, t.e1, t.e2)

    def Index(self, t, p):
        return wrap(postfix_prec, p,
                    '%s[%s]' % (self(t.e1, postfix_prec),
                                self(t.e2, 0)))

    def Call(self, t, p):
        return wrap(postfix_prec, p,
                    '%s(%s)' % (self(t.e1, postfix_prec),
                                ', '.join(self(e, elem_prec)
                                          for e in t.args)))

    def Dot(self, t, p):
        if isinstance(t.e1, ast.Deref):
            s = '%s->%s' % (self(t.e1.e1, postfix_prec), t.field)
        else:
            s = '%s.%s' % (self(t.e1, postfix_prec), t.field)
        return wrap(postfix_prec, p, s)

    def And(self, t, p):
        return fmt2(p, '&&', t.e1, t.e2)

    def Or(self, t, p):
        return fmt2(p, '||', t.e1, t.e2)

    def Compound_exp(self, t, p):
        # XXX I think C imposes restrictions on where this can appear?
        # Also, the indentation might be awful without more work
        return embrace(c_exp(e, elem_prec) + ',' for e in t.exps)

c_exp_emitter = CExpEmitter()


# Parenthesizing by precedence

infix_precedence_tower = """\
,
=
?:
||
&&
|
^
&
== !=
< > <= >=
<< >>
+ -
* / %
(cast)
(unary)
(postfix)""".splitlines()

binaries = {op: (2*i, 2*i+1)
            for i, line in enumerate(infix_precedence_tower)
            for op in line.split()}
cast_prec    = binaries['(cast)'][0]
unary_prec   = binaries['(unary)'][0]
postfix_prec = binaries['(postfix)'][0]

elem_prec    = binaries['='][0]  # The next precedence after ','
# Make the left precedence of the assignment operator be unary_expression, and right-associative:
binaries['='] = (unary_prec, binaries['='][0])

# Also, ?: is also right-associative:
binaries['?:'] = (binaries['?:'][0], binaries['?:'][0])

def fmt1(outer, inner, fmt_str, e1):
    return wrap(inner, outer, fmt_str % c_exp(e1, inner))

def fmt2(p, op, e1, e2, fmt_str='%s %s %s'):
    lp, rp = binaries['=' if op.endswith('=') else op]
    return wrap(lp, p, fmt_str % (c_exp(e1, lp), op, c_exp(e2, rp)))

def wrap(inner, outer, s):
    return '(%s)' % s if inner < outer else s
