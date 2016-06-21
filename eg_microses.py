"""
Let's try and port
~/othergit/quasiParserGenerator/test/microses/microses.es6
"""

from parson import Grammar

g = r""" body :end.

# Exclude "arguments" from IDENT in microses.
# XXX defnordify
RESERVED_WORD:
             KEYWORD | ES6_ONLY_KEYWORD | FUTURE_RESERVED_WORD
           | "arguments".

KEYWORD:     "false" | "true"
           | "break" | "case" | "catch" | "const"
           | "debugger" | "default" | "delete"
           | "else" | "export" | "finally"
           | "for" | "if" | "import"
           | "return" | "switch" | "throw" | "try"
           | "typeof" | "void" | "while".

# We enumerate these anyway, in order to exclude them from the
# IDENT token.
ES6_ONLY_KEYWORD:
             "null" | "class" | "continue" | "do" | "extends"
           | "function" | "in" | "instanceof" | "new" | "super"
           | "this" | "var" | "with" | "yield".

FUTURE_RESERVED_WORD:
             "enum" | "await"
           | "implements" | "interface" | "package"
           | "private" | "protected" | "public".


primaryExpr: (NUMBER | STRING | {"true" | "false" | "null"})   :Data   # XXX do it my way instead? also, "null" was missing in the original
           | '[' arg ** ',' ']'                :hug :Array
           | '{' prop ** ',' '}'               :hug :Object
           | quasiExpr
           | '(' expr ')'
           | IDENT                                  :Variable
           | HOLE                                   :ExprHole.

pattern:     (NUMBER | STRING | {"true" | "false" | "null"})   :MatchData # XXX ditto
           | '[' param ** ',' ']'              :hug :MatchArray
           | '{' propParam ** ',' '}'          :hug :MatchObject
           | IDENT                                  :MatchVariable
           | HOLE                                   :PatternHole.

arg:         '...' expr                             :Spread
           | expr.

param:       '...' pattern                          :Rest
           | IDENT '=' expr                         :Optional
           | pattern.

# No method definition.  XXX why not?
prop:        '...' expr                             :SpreadObj
           | key ':' expr                           :Prop
           | IDENT :None                            :Prop.

propParam:  '...' pattern                           :RestObj
           | key ':' pattern                        :MatchProp
           | IDENT '=' expr                         :OptionalProp
           | IDENT :None                            :MatchProp.   # ditto

key:         IDENT | RESERVED_WORD | STRING | NUMBER
           | '[' expr ']'                           :Computed.

# XXX look up es6 quasiliteral syntax
quasiExpr ~: '`' qfill ** qhole '`' FNORD :hug      :Quasi.
qfill     ~: {(!'`' !'${' :anyone)*}.
qhole     ~: '${' FNORD expr '}'.

later:       NO_NEWLINE '!'.

# No "new", "super", or MetaProperty. Without "new" we don't need
# separate MemberExpr and CallExpr productions.
postExpr:    primaryExpr postOp*.
postOp     = '.' IDENT                              :Get
           | '[' expr ']'                           :Index
           | '(' [arg**',' :hug] ')'                :Call
           | quasiExpr                              :Tag
           | later ( IDENT                          :GetLater
                   | '[' expr ']'                   :IndexLater
                   | '(' [arg**',' :hug] ')'        :CallLater
                   | quasiExpr                      :TagLater ).

preExpr:     "delete" fieldExpr                     :Delete
           | preOp preExpr                          :UnaryOp
           | postExpr.

# No prefix or postfix "++" or "--".
preOp:       { "void" | "typeof" | '+' | '-' | '!' }.  # XXX strip

# No bitwise operators, "instanceof", or "in".  Unlike ES6, none
# of the relational operators associate. To help readers, mixing
# relational operators always requires explicit parens.
multExpr:    preExpr ({'*' | '|' | '%'} preExpr :BinaryOp)*.
addExpr:     multExpr ({'+' | '-'} multExpr :BinaryOp)*.
relExpr:     addExpr (relOp addExpr :BinaryOp)?.
relOp:       { '<=' | '>=' | '<' | '>' | '===' | '!==' }.
andThenExpr: relExpr ('&&' relExpr :AndThen)*.
orElseExpr:  andThenExpr ('||' andThenExpr :OrElse)*.

# No trinary ("?:") expression
# No comma expression, so assignment expression is expr.
expr:        lValue assignOp expr                   :Assign
           | arrow
           | orElseExpr.

lValue:      fieldExpr | IDENT.  # (out of order in the original)

fieldExpr:   primaryExpr
               ( '.' IDENT                          :Get
               | '[' expr ']'                       :Index
               | later ( '.' IDENT                  :GetLater
                       | '[' expr ']'               :IndexLater ) ).

assignOp:    {'=' !'='  # (the ! is implicit in the original?)
             | '*=' | '/=' | '%=' | '+=' | '-='}.

arrow:       params :hug NO_NEWLINE '=>' ( block    :Arrow
                                         | expr     :Lambda ).

params:      IDENT
           | '(' param ** ',' ')'.

# No "var", empty statement, "continue", "with", "do/while",
# "for/in", or labelled statement. None of the insane variations
# of "for". Only blocks are accepted for flow-of-control
# statements.
statement:   block
           | "if" '(' expr ')'
               block
               ("else" block | :None)               :If
           | "for" '(' declaration
                      (expr|:None) ';'
                      (expr|:None) ')'
               block                                :For
           | "for" '(' declOp binding "of" expr ')'
               block                                :ForOf
           | "while" '(' expr ')' block             :While
           | "try" block catcher (finalizer|:None)  :Try
           | "try" block :None   finalizer          :Try
           | "switch" '(' expr ')'
               '{' [branch* :hug] '}'               :Switch
           | terminator
           | "debugger" ';'                         :Debugger
           | expr ';'.

# Each case branch must end in a terminating statement. No
# labelled break.
terminator:  "return" NO_NEWLINE expr ';'           :Return
           | "return" :None ';'                     :Return
           | "break" ';'                            :Break
           | "throw" expr ';'                       :Throw.

# no "function", generator, or "class" declaration.
declaration: declOp [binding ** ',' :hug] ';'       :Decl.
declOp:      {"const"|"let"}.    # XXX must be stripped
# Initializer is mandatory
binding:     pattern '=' expr                       :hug.

catcher:     "catch" '(' pattern ')' block          :hug.
finalizer:   "finally" block.

branch:      caseLabel+ :hug
               '{' body terminator '}'              :Branch.
caseLabel:   "case" expr ':'                        :Case
           | "default" ':'                          :Default.

block:       '{' body '}'                           :Block.
body:        (statement | declaration)*             :hug.

FNORD      ~: space*.
space      ~: /\s+|\/\/.*/ | '/*' (!'*/' :anyone)* '*/'.

NO_NEWLINE ~: . # XXX
HOLE       ~: 'XXX I will be a hole'.

NUMBER      : /(\d+)/.   # XXX
STRING     ~: /"([^"]*)"/ FNORD # XXX
            | /'([^']*)'/ FNORD.
IDENT      ~: !RESERVED_WORD {IdentifierName} FNORD.

# XXX incomplete
IdentifierName   ~= IdentifierStart IdentifierPart*.
IdentifierStart  ~= UnicodeLetter
                  | '$'
                  | '_'.
IdentifierPart   ~= IdentifierStart.
UnicodeLetter    ~= /[A-Za-z]/.

"""

#import sys; sys.setrecursionlimit(5000)
gr = Grammar(g)
import microses
grr = gr.bind(microses).expecting_one_result()

def test(filename):
    from pprint import pprint
    print 'testing', filename
    with open(filename) as f:
        text = f.read()
    result = grr(text)
    for form in result:
        pprint(form.as_sexpr())

## grr('a.b =c;')
#. (Assign(Get(Variable('a'), 'b'), '=', Variable('c')),)

## test('es6/a.es6')
#. testing es6/a.es6
#. ('Decl',
#.  'let ',
#.  ((('MatchVariable', 'a'),
#.    ('BinaryOp',
#.     ('Get', ('Variable', 'module'), 'exports'),
#.     '*',
#.     ('Data', '2'))),))
#. ('Assign', ('Get', ('Variable', 'module'), 'exports'), '= ', ('Data', '5'))
