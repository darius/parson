"""
Convert a Peglet grammar to a Parson one.
"""

import re
from parson import Grammar, alter

name = r'[A-Za-z_]\w*'

grammar = Grammar(r"""
grammar ::= _? rule*.
rule    ::= name _ '= ' :equ token* [:dot] _?.
token   ::= '|'                     :bar
         |  /(\/\w*\/\s)/
         |  name ~(_ '= ')
         |  '!'                     :inv
         |  _ ~(name _ '= ' | ~/./)
         |  ~('= '|name) /(\S+)/    :regex.
name    ::= /("""+name+""")/.
_       ::= /(\s+)/.
""")
actions = dict(dot   = lambda: '.',
               bar   = lambda: '  | ',
               inv   = lambda: '~',
               regex = lambda s: '/' + s.replace('/', '\\/') + '/')

def peglet_to_parson(text):
    nonterminals = set()
    def equ(name, space):
        nonterminals.add(name)
        return name, space, '::= '
    g = grammar(equ=alter(equ), **actions)
    tokens = g.grammar(text)
    return ''.join(':'+token if re.match(name+'$', token) and token not in nonterminals
                   else token
                   for token in tokens)

if __name__ == '__main__':
    import sys
    print peglet_to_parson(sys.stdin.read())
