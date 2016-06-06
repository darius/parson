"""
Convert a Peglet grammar to a Parson one.
"""

import re
from parson import Grammar, alter

name = r'[A-Za-z_]\w*'

grammar = Grammar(r"""
grammar  :  _? rule* :end.
rule     :  name _ '= ' :equ token* :'.' _?.
token    :  '|'                     :'|'
         |  /(\/\w*\/\s)/
         |  name !(_ '= ')
         |  '!'                     :'!'
         |  _ !(name _ '= ' | :end)
         |  !('= '|name) /(\S+)/    :mk_regex.
name     :  /("""+name+""")/ !!(/\s/ | :end).
_        :  /(\s+)/.
""")
def mk_regex(s): return '/' + s.replace('/', '\\/') + '/'

def peglet_to_parson(text):
    nonterminals = set()
    def equ(name, space):
        nonterminals.add(name)
        return name, space, ': '
    g = grammar(equ=alter(equ), mk_regex=mk_regex)
    tokens = g.grammar(text)
    return ''.join(':'+token if re.match(name+'$', token) and token not in nonterminals
                   else token
                   for token in tokens)

if __name__ == '__main__':
    import sys
    print peglet_to_parson(sys.stdin.read())
