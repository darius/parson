"""
Tie the modules together into a compiler.
It writes VM assembly to stdout.
"""

import sys

import ast
from gen_vm_asm import gen_program
from parson import Grammar, Unparsable

with open('b2020.parson') as f:
    grammar_source = f.read()
parser = Grammar(grammar_source).bind(ast)

def main(argv):
    err = 0
    for filename in argv[1:]:
        err |= compiler_main(filename)
    return err

def compiler_main(filename, out_filename=None):
    with open(filename) as f:
        text = f.read()
    try:
        global_decls = parser.program(text)
    except Unparsable as exc:
        (before, after) = exc.failure
        complain(filename, before, after, "Syntax error")
        return 1
    gen_program(global_decls)
    return 0

def complain(filename, before, after, plaint):
    line_no = before.count('\n')
    prefix = (before+'\n').splitlines()[line_no]
    suffix = (after+'\n').splitlines()[0] # XXX what if right on newline?
    prefix, suffix = sanitize(prefix), sanitize(suffix)
    message = ["%s:%d:%d: %s" % (filename, line_no+1, len(prefix), plaint),
               '  ' + prefix + suffix,
               '  ' + ' '*len(prefix) + '^']
    sys.stderr.write('\n'.join(message) + '\n')

def sanitize(s):
    "Make s predictably printable, sans control characters like tab."
    unprintable = chr(127)
    return ''.join(c if ' ' <= c < unprintable else ' ' # XXX crude
                   for c in s)
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
