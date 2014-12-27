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

## import glob
## for filename in glob.glob('ob/*.ob'): test(filename)
#. testing ob/badarg.ob
#. testing ob/proc.ob
#. testing ob/gcd.ob
#. testing ob/type.ob
#. testing ob/simpleexps.ob
#. testing ob/whilename.ob
#. testing ob/badwhile.ob
#. testing ob/nonintconstant.ob
#. testing ob/factorial.ob
#. testing ob/selfref.ob
#. testing ob/comment.ob
#. testing ob/badproc.ob
#. testing ob/const.ob
#. testing ob/arrayname.ob
#. testing ob/badcond.ob
#. testing ob/recurse.ob
#. testing ob/recordname.ob
#. testing ob/emptydeclsections.ob
#. testing ob/redefinteger.ob
#. testing ob/nonlocalvar.ob
#. testing ob/badrecord.ob
#. testing ob/nominalarg.ob
#. testing ob/badarray.ob
#. testing ob/typenodecl.ob
#. testing ob/badeq.ob
#. testing ob/cond.ob
#. testing ob/emptymodule.ob
#. testing ob/while.ob
#. testing ob/wrongprocedurename.ob
#. testing ob/keywordprefix.ob
#. testing ob/nonmoduleasmodulename.ob
#. testing ob/assign.ob
#. testing ob/wrongmodulename.ob
#. testing ob/var.ob
#. testing ob/intoverflow.ob
#. testing ob/emptybody.ob
#. testing ob/redeftrue.ob
#. testing ob/condname.ob

## test('oberon/Oberon-0/input.txt')
#. testing oberon/Oberon-0/input.txt
## test('oberon/Oberon-0/examples/fibonacci.obr')
#. testing oberon/Oberon-0/examples/fibonacci.obr
## test('oberon/Oberon-0/examples/fibonacci_r.obr')
#. testing oberon/Oberon-0/examples/fibonacci_r.obr
## test('oberon/Oberon-0/examples/gcd.obr')
#. testing oberon/Oberon-0/examples/gcd.obr



def test(filename):
    print 'testing', filename
    with open(filename) as f:
        text = f.read()
    grammar.top(text)

## ob = open('ob/arrayname.ob').read()
## print ob
#. MODULE arrayname;
#. 
#. TYPE
#.     atype1 = ARRAY 10 OF atype0;
#.     atype2 = ARRAY 3 * aconst OF INTEGER;
#. 
#. END arrayname.
#. 
## grammar.module(ob)
#. ('arrayname', 'atype1', 10, 'atype0', 'atype2', 3, 'aconst', 'INTEGER', 'arrayname')
