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
relation:             '='_ | '#'_ | '<'_ | '<='_ | '>'_ | '>='_.
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
FPSection:            'VAR'? IdentList ':'_ type.
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

_:                    /\s*/.
keyword:              /BEGIN|END|MODULE|VAR|TYPE|CONST|PROCEDURE|RECORD|ARRAY|OF|WHILE|DO|IF|ELSIF|THEN|ELSE|OR|DIV|MOD/ /\b/.
top:                  _ module ~/./.
"""

grammar = Grammar(grammar_source)()
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
