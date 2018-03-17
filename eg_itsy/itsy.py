"""
Tie the modules together into a compiler.
"""

from parson import Grammar
import ast

with open('grammar') as f:
    grammar_source = f.read()
parse = Grammar(grammar_source).bind(ast)

with open('c_prelude.h') as f:
    c_prelude = f.read()

from c_emitter import decl_emitter

def to_c_main(filename, out_filename=None):
    if out_filename is None:
        if not filename.endswith('.itsy'):
            raise Exception("Missing output filename")
        out_filename = filename[:-len('.itsy')] + '.c'
    with open(filename) as f:
        source = f.read()
    c = c_from_itsy(source, filename)
    with open(out_filename, 'w') as f:
        f.write(c)

def c_from_itsy(source, filename=''):
    # TODO errors, error messages
    defs = parse.top(source)
    c_defs = map(decl_emitter, defs)
    return c_prelude + '\n' + '\n\n'.join(c_defs) + '\n'

if __name__ == '__main__':
    import sys
    assert 2 <= len(sys.argv) <= 3, "usage: itsy.py source_file.itsy [output_c_file.c]"
    to_c_main(*sys.argv[1:])
