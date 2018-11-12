"""
A template language, similar to templite by Ned Batchelder.
https://github.com/aosabook/500lines/tree/master/template-engine
(Still missing a few features.)
"""

from parson import Grammar
from structs import Struct, Visitor

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

class Block(Struct('chunks')): pass
class Literal(Struct('string')): pass
class If(Struct('expr block')): pass
class For(Struct('variable expr block')): pass
class Expr(Struct('expr')): pass
class VarRef(Struct('variable')): pass
class Access(Struct('base attribute')): pass
class Call(Struct('operand function')): pass

parse = Grammar(grammar)(**globals()).expecting_one_result()

def compile_template(text):
    code = gen(parse(text))
    env = {}
    exec(code, env)
    return env['_expand']

def gen(template):
    py = """\
def _expand(_context):
    _acc = []
    _append = _acc.append
    %s
    %s
    return ''.join(_acc)"""
    decls = '\n'.join('v_%s = _context[%r]' % (name, name)
                      for name in free_vars(template))
    return py % (indent(decls), indent(gen_visitor(template)))

class Gen(Visitor):
    def Block(self, t):   return '\n'.join(map(self, t.chunks))
    def Literal(self, t): return '_append(%r)' % t.string
    def If(self, t):      return ('if %s:\n    %s'
                                  % (self(t.expr),
                                     indent(self(t.block))))
    def For(self, t):     return ('for v_%s in %s:\n    %s'
                                  % (t.variable, self(t.expr),
                                     indent(self(t.block))))
    def Expr(self, t):    return '_append(str(%s))' % self(t.expr)
    def VarRef(self, t):  return 'v_%s' % t.variable
    def Access(self, t):  return '%s.%s' % (self(t.base), t.attribute)
    def Call(self, t):    return '%s(%s)' % (t.function, self(t.operand))

gen_visitor = Gen()

class FreeVars(Visitor):
    def Block(self, t):   return set().union(*map(self, t.chunks))
    def Literal(self, t): return set()
    def If(self, t):      return self(t.expr) | self(t.block)
    def For(self, t):     return ((self(t.expr) | self(t.block))
                                  - set([t.variable]))
    def Expr(self, t):    return self(t.expr)
    def VarRef(self, t):  return set([t.variable])
    def Access(self, t):  return self(t.base)
    def Call(self, t):    return self(t.operand)

free_vars = FreeVars()

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

## f = compile_template('hello {%for x in xs%} whee{{x}} {% endfor %} yay'); print f(dict(xs='abc'))
#. hello  wheea  wheeb  wheec  yay

## f = compile_template(' {%if x%} whee{{x}} {% endif %} yay {%if y%} ok{{y}} {% endif %}'); print f(dict(x='', y='42'))
#.   yay  ok42 
