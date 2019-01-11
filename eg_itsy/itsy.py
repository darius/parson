"""
Tie the modules together into a compiler.
"""

import ast
from parson import Grammar, Unparsable
from complainer import Complainer
from c_emitter import c_emit
import primitives
import typecheck
import sys

with open('grammar') as f:
    grammar_source = f.read()
parser = Grammar(grammar_source).bind(ast)

with open('c_prelude.h') as f:
    c_prelude = f.read()


def main(argv):
    assert 2 <= len(argv), "usage: %s source_file.itsy [output_file.c]" % argv[0]
    return to_c_main(*argv[1:])

def to_c_main(filename, out_filename=None):
    if out_filename is None:
        stem = filename[:-len('.itsy')] if filename.endswith('.itsy') else filename
        out_filename = stem + '.c'
    with open(filename) as f:
        text = f.read()
    opt_c = c_from_itsy(Complainer(text, filename))
    if opt_c is None:
        return 1
    with open(out_filename, 'w') as f:
        f.write(opt_c)
    return 0

def c_from_itsy(complainer):
    try:
        defs = parser.top(complainer.text)
    except Unparsable as exc:
        complainer.syntax_error(exc)
        return None
    typecheck.check(defs, primitives.prims, complainer)
    if not complainer.ok():
        return None
    c_defs = map(c_emit, defs)
    return c_prelude + '\n' + '\n\n'.join(c_defs) + '\n'


if __name__ == '__main__':
    sys.exit(main(sys.argv))
