"""
A template language, similar to templite by Ned Batchelder.
https://github.com/aosabook/500lines/tree/master/template-engine
"""

from parson import Grammar
from structs import Struct

grammar = r"""  block :end.

block:     chunk* :hug :Block.

chunk:     '{#' (!'#}' /./)* '#}'
        |  '{{'_ expr '}}'                                                   :Expr
        |  '{%'_ 'if'_ expr '%}'                block '{%'_ 'endif'_  '%}'   :If
        |  '{%'_ 'for'_ ident _ 'in'_ expr '%}' block '{%'_ 'endfor'_ '%}'   :For
        |  (!/{[#{%]/ /(.)/)+ :join                                          :Literal .

expr:      access ('|' function :Call)* _ .
access:    ident :VarRef ('.' ident :Access)*.
function:  ident.

ident:     /([A-Za-z_][A-Za-z_0-9]*)/.

_:         /\s*/.
"""

class Block(Struct('chunks')):
    def gen(self):
        return '\n'.join(chunk.gen() for chunk in self.chunks)

class Literal(Struct('string')):
    def gen(self):
        return '_append(%r)' % self.string

class If(Struct('expr block')):
    def gen(self, code):
        return ('if %s:\n    %s'
                % (self.expr.gen(), indent(self.block.gen())))

class For(Struct('variable expr block')):
    def gen(self, code):
        return ('for %s in %s:\n    %s'
                % (self.variable, self.expr.gen(), indent(self.block.gen())))

class Expr(Struct('expr')):
    def gen(self):
        return '_append(str(%s))' % self.expr.gen()

class VarRef(Struct('variable')):
    def gen(self):
        return '_context[%r]' % self.variable

class Access(Struct('base attribute')):
    def gen(self):
        return '%s.%s' % (self.base.gen(), self.attribute)

class Call(Struct('operand function')):
    def gen(self):
        return '%s(%s)' % (self.function, self.operand.gen())

parse = Grammar(grammar)(**globals()).expecting_one_result()

def compile_template(text):
    template = parse(text)
    code = gen(template)
    env = {}
    exec(code, env)
    return env['_expand']

def gen(template):
    t = """\
def _expand(_context):
    _acc = []
    _append = _acc.append
    %s
    return ''.join(_acc)"""
    return t % indent(template.gen())

def indent(s):
    return s.replace('\n', '\n    ')

## parse('hello {{world}} yay')
#. Block((Literal('hello '), Expr(VarRef('world')), Literal(' yay')))

## print gen(parse('hello {{world}} yay'))
#. def _expand(_context):
#.     _acc = []
#.     _append = _acc.append
#.     _append('hello ')
#.     _append(str(_context['world']))
#.     _append(' yay')
#.     return ''.join(_acc)

## f = compile_template('hello {{world}} yay'); print f(dict(world="globe"))
#. hello globe yay
