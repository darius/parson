"""
The Oberon-0 programming language.
Wirth, _Compiler Construction_, Appendix A.
"""

from parson import Grammar

grammar_source = r"""
ident:                ~keyword /([A-Za-z][A-Za-z0-9]*)\b/_.
integer:              digit+ :join :int.
digit:                /(\d)/_.
selector:             ('.'_ ident | '['_ expression ']'_)*.
factor:               ident selector
                    | integer
                    | '('_ expression ')'_
                    | '~'_ factor.
term:                 factor (MulOperator factor)*.
MulOperator:          '*'_ | 'DIV'_ | 'MOD'_ | '&'_.
SimpleExpression:     ('+'_|'-'_)? term (AddOperator term)*.
AddOperator:          '+'_ | '-'_ | 'OR'_.
expression:           SimpleExpression (relation SimpleExpression)?.
relation:             '='_ | '#'_ | '<='_ | '<'_ | '>='_ | '>'_.
assignment:           ident selector ':='_ expression.
ActualParameters:     '('_ ExpList? ')'_.
ExpList:              expression (','_ expression)*.
ProcedureCall:        ident ActualParameters?.
IfStatement:          'IF'_ expression 'THEN'_ StatementSequence
                      ('ELSIF'_ expression 'THEN'_ StatementSequence)*
                      ('ELSE'_ StatementSequence)?
                      'END'_.
WhileStatement:       'WHILE'_ expression 'DO'_ StatementSequence 'END'_.
statement:            (assignment | ProcedureCall | IfStatement | WhileStatement)?.
StatementSequence:    statement (';'_ statement)*.
IdentList:            ident (','_ ident)*.
ArrayType:            'ARRAY'_ expression 'OF'_ type.
FieldList:            (IdentList ':'_ type)?.
RecordType:           'RECORD'_ FieldList (';'_ FieldList)* 'END'_.
type:                 ident | ArrayType | RecordType.
FPSection:            ('VAR'_)? IdentList ':'_ type.
FormalParameters:     '('_ (FPSection (';'_ FPSection)*)? ')'_.
ProcedureHeading:     'PROCEDURE'_ ident FormalParameters?.
ProcedureBody:        declarations ('BEGIN'_ StatementSequence)? 'END'_.
ProcedureDeclaration: ProcedureHeading ';'_ ProcedureBody ident.
declarations:         ('CONST'_ (ident '='_ expression ';'_)*)?
                      ('TYPE'_ (ident '='_ type ';'_)*)?
                      ('VAR'_ (IdentList ':'_ type ';'_)*)?
                      (ProcedureDeclaration ';'_)*.
module:               'MODULE'_ ident ';'_ declarations
                      ('BEGIN'_ StatementSequence)? 'END'_ ident '.'_.

_:                    whitespace*.
whitespace:           /\s+/ | comment.
comment:              '(*' commentchunk* '*)'.
commentchunk:         comment | ~'*)' /.|\n/.   # XXX are comments nested in Oberon-0?
keyword:              /BEGIN|END|MODULE|VAR|TYPE|CONST|PROCEDURE|RECORD|ARRAY|OF|WHILE|DO|IF|ELSIF|THEN|ELSE|OR|DIV|MOD/ /\b/.
top:                  _ module ~/./.
"""
grammar = Grammar(grammar_source)()

# TODO test for expected parse failures

## from parson import exceptionally
## import glob

## for filename in sorted(glob.glob('ob-bad/*.ob')): print exceptionally(lambda: test(filename))
#. testing ob-bad/badassign.ob
#. (top, 'MODULE badassign;\n\nBEGIN\n    ', '1 := 2\nEND badassign.\n')
#. testing ob-bad/commentnoend.ob
#. (top, "MODULE commentnoend;\n (* started off well,\n   but didn't finish\nEND commentnoend.\n", '')
#. testing ob-bad/keywordasname.ob
#. (top, 'MODULE ', 'END;\nEND END.\n')
#. testing ob-bad/repeatsection.ob
#. (top, 'MODULE repeatsection;\n\nCONST\n    aconst = 10;\n\n', 'CONST\n    aconst = 20;\n\nEND repeatsection.\n')

## for filename in sorted(glob.glob('ob-ok/*.ob')): test(filename)
#. testing ob-ok/arrayname.ob
#. testing ob-ok/assign.ob
#. testing ob-ok/badarg.ob
#. testing ob-ok/badarray.ob
#. testing ob-ok/badcond.ob
#. testing ob-ok/badeq.ob
#. testing ob-ok/badproc.ob
#. testing ob-ok/badrecord.ob
#. testing ob-ok/badwhile.ob
#. testing ob-ok/comment.ob
#. testing ob-ok/cond.ob
#. testing ob-ok/condname.ob
#. testing ob-ok/const.ob
#. testing ob-ok/emptybody.ob
#. testing ob-ok/emptydeclsections.ob
#. testing ob-ok/emptymodule.ob
#. testing ob-ok/factorial.ob
#. testing ob-ok/gcd.ob
#. testing ob-ok/intoverflow.ob
#. testing ob-ok/keywordprefix.ob
#. testing ob-ok/nominalarg.ob
#. testing ob-ok/nonintconstant.ob
#. testing ob-ok/nonlocalvar.ob
#. testing ob-ok/nonmoduleasmodulename.ob
#. testing ob-ok/proc.ob
#. testing ob-ok/recordname.ob
#. testing ob-ok/recurse.ob
#. testing ob-ok/redefinteger.ob
#. testing ob-ok/redeftrue.ob
#. testing ob-ok/selfref.ob
#. testing ob-ok/simpleexps.ob
#. testing ob-ok/type.ob
#. testing ob-ok/typenodecl.ob
#. testing ob-ok/var.ob
#. testing ob-ok/while.ob
#. testing ob-ok/whilename.ob
#. testing ob-ok/wrongmodulename.ob
#. testing ob-ok/wrongprocedurename.ob

## test('oberon/Oberon-0/input.txt')
#. testing oberon/Oberon-0/input.txt
## for filename in sorted(glob.glob('oberon/Oberon-0/examples/*.obr')): test(filename)
#. testing oberon/Oberon-0/examples/fibonacci.obr
#. testing oberon/Oberon-0/examples/fibonacci_r.obr
#. testing oberon/Oberon-0/examples/gcd.obr

def test(filename):
    print 'testing', filename
    with open(filename) as f:
        text = f.read()
    grammar.top(text)
