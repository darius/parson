"""
Emit C code from an AST.
"""

from structs import Visitor

def indent(s):
    return s.replace('\n', '\n    ')

def embrace(lines):
    return '{\n    %s\n}' % indent('\n'.join(lines))

def opt_c_exp(opt_e, if_none, if_some, p=0):
    return if_none if opt_e is None else if_some % c_exp(opt_e, p)


# Declarations
# TODO rename to avoid confusion with c_decl below

class DeclEmitter(Visitor):

    def Let(self, t):
        if t.opt_exp is not None and len(t.names) != 1:
            raise Exception("XXX yadda yadda")
        assign = opt_c_exp(t.opt_exp, '', ' = %s', list_context)
        return '\n'.join('%s%s;' % (c_decl(t.type, name), assign)
                         for name in t.names)

    def Array_decl(self, t):
        return '%s = %s;' % (c_decl(t.type, t.name),
                             embrace(c_exp(e, list_context) + ','
                                     for e in t.exps))

    def Enum(self, t):
        # XXX is this right when we mix explicit and implicit values?
        enums = ['%s%s,' % (name, opt_c_exp(opt_exp, '', ' = %s'))
                 for name, opt_exp in t.pairs]
        return 'enum %s%s;' % (t.opt_name + ' ' if t.opt_name else '',
                               embrace(enums))

    def To(self, t):
        return_type = ('void' if t.opt_return_type is None
                       else c_type(t.opt_return_type))
        params_c = ', '.join(c_decl(type_, name)
                             for names, type_ in t.params
                             for name in names)
        return '%s %s(%s) %s' % (return_type,
                                 t.name,
                                 params_c or 'void',
                                 c_stmt(t.body))

decl_emitter = DeclEmitter()


# Types

def c_decl(type_, name):
    return '%s %s' % decl_pair(type_, name)

class DeclPair(Visitor):

    def default(self, t, e):
        return c_type(t), e

    def Pointer(self, t, e):
        return self(t.type, '(*%s)' % e)

    def Array(self, t, e):
        a, b = self(t.type, e)
        return a, '%s[%s]' % (b, c_exp(t.size, 0))

    def Function(self, t, e):
        return self(t.type, '*%s(%s)' % (e, c_params(t)))

decl_pair = DeclPair()

def c_params(t):
    return ', '.join(map(c_type, t.param_types))

class CType(Visitor):

    def Int(self, t):
        return 'int'            # XXX...

    def Char(self, t):
        return 'char'

    def Void(self, t):
        return 'void'

    def Float(self, t):
        return t.name

    def Type_name(self, t):
        return t.name

    def Pointer(self, t):
        return '*%s' % self(self.type) # XXX right? also XXX parentheses sometimes, here and below

    def Array(self, t):
        return '%s[%s]' % (self(t.type), c_exp(t.size, 0))

    def Function(self, t):
        return '(%s)(%s)' % (c_type(t.return_type), c_params(t))

c_type = CType()


# Statements

class CStmt(Visitor):

    def Exp(self, t):
        return opt_c_exp(t.opt_exp, ';', '%s;')

    def Return(self, t):
        return opt_c_exp(t.opt_exp, 'return;', 'return %s;')

    def Break(self, t):
        return 'break;'

    def Continue(self, t):
        return 'continue;'

    def While(self, t):
        return 'while (%s) %s' % (c_exp(t.exp, 0), c_stmt(t.block))

    def Do(self, t):
        return 'do %s while(%s)' % (c_stmt(t.block), c_exp(t.exp, 0))

    def Ifs(self, t):
        clauses = zip(t.parts[0:-1:2], t.parts[1::2])
        else_block = t.parts[-1]
        ifs = ' else '.join('if (%s) %s' % (c_exp(exp, 0), c_stmt(block))
                            for exp, block in clauses)
        return ifs + ('' if else_block is None
                      else ' else %s' % c_stmt(else_block))

    def For(self, t):
        e1 = opt_c_exp(t.opt_e1, '', '%s')
        e2 = opt_c_exp(t.opt_e2, '', '%s')
        e3 = opt_c_exp(t.opt_e3, '', '%s')
        return 'for (%s; %s; %s) %s' % (e1, e2, e3, c_stmt(t.block))

    def Switch(self, t):
        return 'switch (%s) %s' % (c_exp(t.exp, 0),
                                   embrace(map(c_stmt, t.cases)))

    def Case(self, t):          # XXX not actually a stmt
        cases = '\n'.join('case %s:' % c_exp(e, 0) for e in t.exps)
        return '%s %s break;' % (cases, c_stmt(t.block))

    def Default(self, t):
        return 'default: %s break;' % c_stmt(t.block)

    def Block(self, t):
        return embrace(map(decl_emitter, t.decls)
                       + map(c_stmt, t.stmts))

c_stmt = CStmt()


# Expressions

class CExp(Visitor):

    def Literal(self, t, p):
        return repr(t.value)

    def String(self, t, p):
        return '"%s"' % t.value       # XXX escaping as C

    def Char_literal(self, t, p):
        return "'%s'" % t.value    # XXX escaping

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
                                               c_exp(t.exp, cast_prec)))

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
                    '%s ? %s : %s' % (c_exp(t.e1, lp),
                                      c_exp(t.e2, 0),
                                      c_exp(t.e3, rp)))

    def Assign(self, t, p):
        return fmt2(p, (t.opt_binop or '') + '=', t.e1, t.e2) # TODO clumsy

    def Binary_exp(self, t, p):
        return fmt2(p, t.binop, t.e1, t.e2)

    def Index(self, t, p):
        return wrap(postfix_prec, p,
                    '%s[%s]' % (c_exp(t.e1, postfix_prec),
                                c_exp(t.e2, 0)))

    def Call(self, t, p):
        return wrap(postfix_prec, p,
                    '%s(%s)' % (c_exp(t.e1, postfix_prec),
                                ', '.join(c_exp(e, list_context)
                                          for e in t.args)))

    def Dot(self, t, p):
        if isinstance(t.e1, Deref):
            s = '%s->%s' % (c_exp(t.e1.exp, postfix_prec), t.field)
        else:
            s = '%s.%s' % (c_exp(t.e1, postfix_prec), t.field)
        return wrap(postfix_prec, p, s)

    def And(self, t, p):
        return fmt2(p, '&&', t.e1, t.e2)

    def Or(self, t, p):
        return fmt2(p, '||', t.e1, t.e2)

c_exp = CExp()


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

list_context = binaries['='][0]  # The next precedence after ','

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
