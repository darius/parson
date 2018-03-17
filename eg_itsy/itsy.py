"""
Tie the modules together into a compiler.
"""

import ast
from parson import Grammar, Unparsable
from parson_plaints import syntax_error
from c_emitter import decl_emitter
import sys

with open('grammar') as f:
    grammar_source = f.read()
parser = Grammar(grammar_source).bind(ast)

with open('c_prelude.h') as f:
    c_prelude = f.read()

def to_c_main(filename, out_filename=None):
    if out_filename is None:
        if not filename.endswith('.itsy'):
            raise Exception("Missing output filename")
        out_filename = filename[:-len('.itsy')] + '.c'
    with open(filename) as f:
        source = f.read()
    try:
        c = c_from_itsy(source, filename)
    except Unparsable as exc:
        sys.stderr.write(syntax_error(exc, filename) + '\n')
        return 1
    # TODO catch semantic errors too
    with open(out_filename, 'w') as f:
        f.write(c)
    return 0

def c_from_itsy(source, filename=''):
    defs = parser.top(source)
    c_defs = map(decl_emitter, defs)
    return c_prelude + '\n' + '\n\n'.join(c_defs) + '\n'


if __name__ == '__main__':
    assert 2 <= len(sys.argv) <= 3, "usage: itsy.py source_file.itsy [output_c_file.c]"
    sys.exit(to_c_main(*sys.argv[1:]))
