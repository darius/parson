"""
Convert a Peglet grammar to a Parson one.
Doesn't do everything: you need to change undefined names to :names in the output.
"""

from parson import Grammar, join

grammar = Grammar(r"""
grammar ::= _? rule*              :join.
rule    ::= id _ ['= ' :equ] token* [:dot] _?.
token   ::= '|'                   :bar
         |  /(\/\w*\/\s)/
         |  id ~(_ '= ')
         |  '!'                   :inv
         |  _ ~(id _ '= ' | ~/./)
         |  ~('= '|id) /(\S+)/    :regex.
id      ::= /([A-Za-z_]\w*)/.
_       ::= /(\s+)/.
""")
parser = grammar(join  = join,
                 equ   = lambda: '::= ',
                 dot   = lambda: '.',
                 bar   = lambda: '  | ',
                 inv   = lambda: '~',
                 regex = lambda s: '/'+s+'/')

if __name__ == '__main__':
    import sys
    print parser.grammar(sys.stdin.read())[0]
