"""
Like eg_oberon0.py, but using a separate lexer.
"""

import re
from parson import Grammar, one_that, label, alter, match

class LexedGrammar(Grammar):
    def __init__(self, string):
        super(LexedGrammar, self).__init__(string)
        self.literals = set()
        self.keywords = set()
    def literal(self, string):
        self.literals.add(string)
        return literal_kind(string)
    def match(self, regex):
        assert False
    def keyword(self, string):
        self.keywords.add(string)
        return literal_kind(string)

def literal_kind(string):
    return one_that(lambda token: token.kind == string)

class Token(object):
    def __init__(self, kind, string):
        self.kind = kind
        self.string = string
    def __repr__(self):
        return repr(self.string)

grammar_source = r"""
selector:             ('.' :IDENT | '[' expression ']')*.
factor:               :IDENT selector
                    | :INTEGER
                    | '(' expression ')'
                    | '~' factor.
term:                 factor ++ MulOperator.
MulOperator:          '*' | "DIV" | "MOD" | '&'.
SimpleExpression:     ('+'|'-')? term ++ AddOperator.
AddOperator:          '+' | '-' | "OR".
expression:           SimpleExpression (relation SimpleExpression)?.
relation:             '=' | '#' | '<=' | '<' | '>=' | '>'.
assignment:           :IDENT selector ':=' expression.
ActualParameters:     '(' expression ** ',' ')'.
ProcedureCall:        :IDENT ActualParameters?.
IfStatement:          "IF" expression "THEN" StatementSequence
                      ("ELSIF" expression "THEN" StatementSequence)*
                      ("ELSE" StatementSequence)?
                      "END".
WhileStatement:       "WHILE" expression "DO" StatementSequence "END".
statement:            (assignment | ProcedureCall | IfStatement | WhileStatement)?.
StatementSequence:    statement ++ ';'.   # XXX isn't it a problem that statement can be empty?
IdentList:            :IDENT ++ ','.
ArrayType:            "ARRAY" expression "OF" type.
FieldList:            (IdentList ':' type)?.
RecordType:           "RECORD" FieldList ++ ';' "END".
type:                 :IDENT | ArrayType | RecordType.
FPSection:            ("VAR")? IdentList ':' type.
FormalParameters:     '(' FPSection ** ';' ')'.
ProcedureHeading:     "PROCEDURE" :IDENT FormalParameters?.
ProcedureBody:        declarations ("BEGIN" StatementSequence)? "END".
ProcedureDeclaration: ProcedureHeading ';' ProcedureBody :IDENT.
declarations:         ("CONST" (:IDENT '=' expression ';')*)?
                      ("TYPE" (:IDENT '=' type ';')*)?
                      ("VAR" (IdentList ':' type ';')*)?
                      (ProcedureDeclaration ';')*.
module:               "MODULE" :IDENT ';' declarations
                      ("BEGIN" StatementSequence)? "END" :IDENT '.'.

top:                  module :end.
"""
builder = LexedGrammar(grammar_source)
grammar = builder(IDENT   = literal_kind('#IDENT'),
                  INTEGER = literal_kind('#INTEGER'))

## builder.keywords
#. set(['THEN', 'BEGIN', 'END', 'DO', 'OF', 'ARRAY', 'MODULE', 'ELSE', 'RECORD', 'WHILE', 'ELSIF', 'VAR', 'CONST', 'DIV', 'MOD', 'TYPE', 'OR', 'PROCEDURE', 'IF'])
## builder.literals
#. set(['#', '<=', '>=', '&', ')', '(', '+', '*', '-', ',', '.', ':=', ':', '=', ';', '[', '>', ']', '<', '~'])

def one_of(strings):
    # Sort longest first because re's '|' matches left-to-right, not greedily:
    alts = sorted(strings, key=len, reverse=True) 
    return '|'.join(map(re.escape, alts))
                        
a_literal = one_of(builder.literals)
a_keyword = one_of(builder.keywords)

lex_grammar_source = r"""  token* :end.
token      :  whitespace | :keyword :Token | :punct :Token | ident | integer.

whitespace :  /\s+/ | comment.
comment    :  '(*' in_comment* '*)'.
in_comment :  comment | !'*)' :anyone.   # XXX are comments nested in Oberon-0?

ident      :  /([A-Za-z][A-Za-z0-9]*)/ :'#IDENT' :Token.
integer    :  /(\d+)/ :'#INTEGER' :Token.
"""
lex_grammar = Grammar(lex_grammar_source)(Token = lambda s, kind=None: Token(kind or s, s),
                                          keyword = match(r'(%s)\b' % a_keyword),
                                          punct   = match(r'(%s)' % a_literal))

## import sys; sys.setrecursionlimit(5000)
## import glob
## from parson import exceptionally

## for filename in sorted(glob.glob('ob-bad/*.ob')): print exceptionally(lambda: test(filename))
#. testing ob-bad/badassign.ob
#. (top, ('MODULE', 'badassign', ';', 'BEGIN'), ('1', ':=', '2', 'END', 'badassign', '.'))
#. testing ob-bad/badcase.ob
#. ((literal('') ((token)* end)), 'MODULE badcase;\n\nVAR\n    avar : INTEGER;\n    bvar : BOOLEAN;\n\nBEGIN\n    CASE bvar OF\n        18 : avar := 19\n    END;\n\n    CASE 1 < 2 OF\n        avar : avar := 3\n      ', '| avar + 1 .. avar + 10 : avar := 5\n    END;\n\n    CASE avar OF\n        3 DIV 0 : avar := 1\n    END\nEND badcase.\n')
#. testing ob-bad/badfor.ob
#. (top, ('MODULE', 'badfor', ';', 'CONST', 'aconst', '=', '10', ';', 'TYPE', 'atype', '=', 'INTEGER', ';', 'VAR', 'avar', ':', 'INTEGER', ';', 'bvar', ':', 'BOOLEAN', ';', 'cvar', ':', 'INTEGER', ';', 'BEGIN', 'FOR'), ('aconst', ':=', '1', 'TO', '10', 'DO', 'avar', ':=', '1', 'END', ';', 'FOR', 'atype', ':=', '1', 'TO', '10', 'DO', 'avar', ':=', '1', 'END', ';', 'FOR', 'bvar', ':=', 'FALSE', 'TO', 'TRUE', 'DO', 'avar', ':=', '42', 'END', ';', 'FOR', 'avar', ':=', '1', 'TO', '2', 'BY', 'cvar', '*', '2', 'DO', 'avar', ':=', '42', 'END', ';', 'FOR', 'dvar', ':=', '1', 'TO', '2', 'DO', 'dvar', ':=', '99', 'END', ';', 'FOR', 'avar', ':=', '8', 'TO', '10', 'BY', '3', 'DIV', '0', 'DO', 'cvar', ':=', '100', 'END', 'END', 'badfor', '.'))
#. testing ob-bad/commentnoend.ob
#. ((literal('') ((token)* end)), "MODULE commentnoend;\n (* started off well,\n   but didn't finish\nEND commentnoend.\n", '')
#. testing ob-bad/keywordasname.ob
#. (top, ('MODULE',), ('VAR', ';', 'END', 'VAR', '.'))
#. testing ob-bad/repeatsection.ob
#. (top, ('MODULE', 'repeatsection', ';', 'CONST', 'aconst', '=', '10', ';'), ('CONST', 'aconst', '=', '20', ';', 'END', 'repeatsection', '.'))

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
#. testing ob-ok/type.ob
#. testing ob-ok/typenodecl.ob
#. testing ob-ok/var.ob
#. testing ob-ok/while.ob
#. testing ob-ok/whilename.ob
#. testing ob-ok/wrongmodulename.ob
#. testing ob-ok/wrongprocedurename.ob

def test(filename):
    print 'testing', filename
    with open(filename) as f:
        text = f.read()
    tokens = lex_grammar(text)
    if 0:
        for token in tokens:
            print token.kind,
        print
    if tokens is not None:
        grammar.top(tokens)
