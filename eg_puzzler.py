"""
Port of ~/git/mccarthy-to-bryant/puzzler.py
Uses modules from that repo (not included in this one).
"""

import operator
from parson import Grammar, Unparsable
import dd

def mk_var(name):
    return dd.Variable(enter(name))

var_names = []
def enter(name):
    try:
        return var_names.index(name)
    except ValueError:
        var_names.append(name)
        return len(var_names) - 1

# This grammar is complicated by requiring that whitespace mean AND
# *only* within a line, not spanning lines -- an implicit AND spanning
# lines would be too error prone.
g = r"""   expr :end.

expr:      sentence (',' expr   :And)?.

sentence:  sum ('=' sum         :Equiv)?.

sum:       term ( '|' sum       :Or
                | '=>' term     :Implies )?.

term:      factor ( term        :And
                  | FNORD ).

factor  ~: '~'_ primary         :Not
         | primary.

primary ~: '(' FNORD expr ')'_
         | id                   :Var.

id      ~: /([A-Za-z_]\w*)/_.

_       ~: /[ \t]*/.    # Spaces within a line.
FNORD   ~: /\s+|#.*/*.  # Spaces/comments that may span lines.
"""

parse = Grammar(g)(Equiv   = dd.Equiv,
                   Implies = dd.Implies,
                   And     = operator.and_,
                   Or      = operator.or_,
                   Not     = operator.inv,
                   Var     = mk_var)

def solve(condition):
    if dd.is_valid(condition):
        print("Valid.")
    else:
        show(dd.satisfy(condition, 1))

def show(opt_env):
    if opt_env is None:
        print("Unsatisfiable.")
    else:
        for k, v in sorted(opt_env.items()):
            if k is not None:
                print("%s%s" % ("" if v else "~", var_names[k]))

## solve(parse(' hey (there | ~there), ~hey | ~there')[0])
#. hey
#. ~there
## solve(parse(' hey (there, ~there)')[0])
#. Unsatisfiable.
## solve(parse('a=>b = ~b=>~a')[0])
#. Valid.


def main(filename, text):
    try:
        problem, = parse(text)
    except Unparsable as e:
        syntax_error(e, filename)
        sys.exit(1)
    else:
        solve(problem)

# TODO: extract something I can stick in the library
#       let's try writing something similar for oberon0-with-lexer, to triangulate

def syntax_error(e, filename):
    line_no, prefix, suffix = where(e)
    prefix, suffix = sanitize(prefix), sanitize(suffix)
    sys.stderr.write("%s:%d:%d: Syntax error\n" % (filename, line_no, len(prefix)))
    sys.stderr.write('  ' + prefix + suffix + '\n')
    sys.stderr.write('  ' + ' '*len(prefix) + '^\n')

def where(e):
    before, after = e.failure
    line_no = before.count('\n')
    prefix = (before+'\n').splitlines()[line_no]
    suffix = (after+'\n').splitlines()[0] # XXX what if right on newline?
    return line_no+1, prefix, suffix

def sanitize(s):
    "Make s predictably printable, sans control characters like tab."
    return ''.join(c if ' ' <= c < chr(127) else ' ' # XXX crude
                   for c in s)


if __name__ == '__main__':
    import sys
    main('stdin', sys.stdin.read())  # (try it on carroll or wise-pigs)
