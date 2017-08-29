"""
A template language, similar to templite by Ned Batchelder.
https://github.com/aosabook/500lines/tree/master/template-engine
(Still missing a few features.)
"""

from parson import Grammar
from structs import Struct

grammar = r"""  block :end.

block:     chunk* :hug :Block.

chunk:     '{#' (!'#}' /./)* '#}'
        |  '{{'_ expr '}}'                                                  :Expr
        |  '{%'_ 'if'_ expr '%}'                block '{%'_ 'endif'_  '%}'  :If
        |  '{%'_ 'for'_ ident _ 'in'_ expr '%}' block '{%'_ 'endfor'_ '%}'  :For
        |  (!/{[#{%]/ /(.)/)+ :join                                         :Literal.

expr:      access ('|' function :Call)* _ .
access:    ident :VarRef ('.' ident :Access)*.
function:  ident.

ident:     /([A-Za-z_][A-Za-z_0-9]*)/.

_:         /\s*/.
"""

class Block(Struct('chunks')):
    def free_vars(self):
        return set().union(*[chunk.free_vars() for chunk in self.chunks])
    def gen(self):
        return '\n'.join(chunk.gen() for chunk in self.chunks)

class Literal(Struct('string')):
    def free_vars(self):
        return set()
    def gen(self):
        return '_append(%r)' % self.string

class If(Struct('expr block')):
    def free_vars(self):
        return self.expr.free_vars() | self.block.free_vars()
    def gen(self):
        return ('if %s:\n    %s'
                % (self.expr.gen(), indent(self.block.gen())))

class For(Struct('variable expr block')):
    def free_vars(self):
        return ((self.expr.free_vars() | self.block.free_vars())
                - set([self.variable]))
    def gen(self):
        return ('for v_%s in %s:\n    %s'
                % (self.variable, self.expr.gen(), indent(self.block.gen())))

class Expr(Struct('expr')):
    def free_vars(self):
        return self.expr.free_vars()
    def gen(self):
        return '_append(str(%s))' % self.expr.gen()

class VarRef(Struct('variable')):
    def free_vars(self):
        return set([self.variable])
    def gen(self):
        return 'v_%s' % self.variable

class Access(Struct('base attribute')):
    def free_vars(self):
        return self.base.free_vars()
    def gen(self):
        return '%s.%s' % (self.base.gen(), self.attribute)

class Call(Struct('operand function')):
    def free_vars(self):
        return self.operand.free_vars()
    def gen(self):
        return '%s(%s)' % (self.function, self.operand.gen())

parse = Grammar(grammar)(**globals()).expecting_one_result()

def compile_template(text):
    code = gen(parse(text))
    env = {}
    exec(code, env)
    return env['_expand']

def gen(template):
    t = """\
def _expand(_context):
    _acc = []
    _append = _acc.append
    %s
    %s
    return ''.join(_acc)"""
    decls = '\n'.join('v_%s = _context[%r]' % (name, name)
                      for name in template.free_vars())
    return t % (indent(decls), indent(template.gen()))

def indent(s):
    return s.replace('\n', '\n    ')

## parse('hello {{world}} yay')
#. Block((Literal('hello '), Expr(VarRef('world')), Literal(' yay')))

## print gen(parse('hello {{world}} yay'))
#. def _expand(_context):
#.     _acc = []
#.     _append = _acc.append
#.     v_world = _context['world']
#.     _append('hello ')
#.     _append(str(v_world))
#.     _append(' yay')
#.     return ''.join(_acc)

## f = compile_template('hello {{world}} yay'); print f(dict(world="globe"))
#. hello globe yay

## print gen(parse('{% if foo.bar %} {% for x in xs|ok %} {{x}} {% endfor %} yay {% endif %}'))
#. def _expand(_context):
#.     _acc = []
#.     _append = _acc.append
#.     v_xs = _context['xs']
#.     v_foo = _context['foo']
#.     if v_foo.bar:
#.         _append(' ')
#.         for v_x in ok(v_xs):
#.             _append(' ')
#.             _append(str(v_x))
#.             _append(' ')
#.         _append(' yay ')
#.     return ''.join(_acc)
