"""
Tie the modules together into a compiler.
"""

import ast
from parson import Grammar, Unparsable
from parson_plaints import syntax_error
from c_emitter import c_emit
import sys

with open('grammar') as f:
    grammar_source = f.read()
parser = Grammar(grammar_source).bind(ast)

with open('c_prelude.h') as f:
    c_prelude = f.read()


def main(argv):
    assert 2 <= len(argv), "usage: %s source_file.itsy [output_c_file.c]" % argv[0]
    return to_c_main(*argv[1:])

def to_c_main(filename, out_filename=None):
    if out_filename is None:
        if not filename.endswith('.itsy'):
            raise Exception("Missing output filename")
        out_filename = filename[:-len('.itsy')] + '.c'
    with open(filename) as f:
        source = f.read()
    try:
        c = c_from_itsy(source)
    except Unparsable as exc:
        sys.stderr.write(syntax_error(exc, filename) + '\n')
        return 1
    # TODO catch semantic errors too
    with open(out_filename, 'w') as f:
        f.write(c)
    return 0

def c_from_itsy(source):
    defs = parser.top(source)
    c_defs = map(c_emit, defs)
    return c_prelude + '\n' + '\n\n'.join(c_defs) + '\n'


if __name__ == '__main__':
    sys.exit(main(sys.argv))
