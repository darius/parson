"""
The Oberon-0 programming language.
Wirth, _Compiler Construction_, Appendix A.
"""

from parson import Grammar

grammar = r"""
ident:                /[A-Za-z]\w*/.   # XXX what's \w? letter|digit?
integer:              digit+.
digit:                /(\d)/.
selector:             ('.' ident | '[' expression ']')*.
factor:               ident selector | integer
                    | '(' expression ')'
                    | '~' factor.
term:                 factor (MulOperator factor)*.
MulOperator:          '*' | 'DIV' | 'MOD' | '&'.
SimpleExpression:     ('+'|'-')? term (AddOperator term)*.
AddOperator:          '+' | '-' | 'OR'.
expression:           SimpleExpression (relation SimpleExpression)?.
relation:             '=' | '#' | '<' | '<=' | '>' | '>='.
assignment:           ident selector ':=' expression.
ActualParameters:     '(' ExpList? ')'.
ExpList:              expression (',' expression)*.
ProcedureCall:        ident ActualParameters?.
IfStatement:          'IF' expression 'THEN' StatementSequence
                      ('ELSIF' expression 'THEN' StatementSequence)*
                      ('ELSE' StatementSequence)?
                      'END'.
WhileStatement:       'WHILE' expression 'DO' StatementSequence 'END'.
statement:            (assignment | ProcedureCall | IfStatement | WhileStatement)?.
StatementSequence:    statement (';' statement)*.
IdentList:            ident (',' ident)*.
ArrayType:            'ARRAY' expression 'OF' type.
FieldList:            (IdentList ':' type)?.
RecordType:           'RECORD' FieldList (';' FieldList)* 'END'.
type:                 ident | ArrayType | RecordType.
FPSection:            'VAR'? IdentList ':' type.
FormalParameters:     '(' (FPSection (';' FPSection)*)? ')'.
ProcedureHeading:     'PROCEDURE' ident FormalParameters?.
ProcedureBody:        declarations ('BEGIN' StatementSequence)? 'END'.
ProcedureDeclaration: ProcedureHeading ';' ProcedureBody ident.
declarations:         ('CONST' (ident '=' expression ';')*)?
                      ('TYPE' (ident '=' type ';')*)?
                      ('VAR' (IdentList ':' type ';')*)?
                      (ProcedureDeclaration ';')*.
module:               'MODULE' ident ';' declarations
                      ('BEGIN' StatementSequence)? 'END' ident '.'.
"""

g = Grammar(grammar)
