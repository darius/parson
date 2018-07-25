"""
Smoke test for parson
"""

from parson import *

# Smoke test: combinators

## empty
#. empty
## fail.attempt('hello')
## empty('hello')
#. ()
## match(r'(x)').attempt('hello')
## match(r'(h)')('hello')
#. ('h',)

## (match(r'(H)') | match('(.)'))('hello')
#. ('h',)
## (match(r'(h)') + match('(.)'))('hello')
#. ('h', 'e')

## (match(r'h(e)') + match(r'(.)'))('hello')
#. ('e', 'l')
## (~match(r'h(e)') + match(r'(.)'))('xhello')
#. ('x',)

## empty.run('', [0], (0, ()))
#. [(0, ())]
## chain(empty, empty)('')
#. ()

## (match(r'(.)') >> hug)('hello')
#. (('h',),)

## match(r'(.)').star()('')
#. ()

## (match(r'(.)').star())('hello')
#. ('h', 'e', 'l', 'l', 'o')

## (match(r'(.)').star() >> join)('hello')
#. ('hello',)


# Example

def make_var(v):         return v
def make_lam(v, e):      return '(lambda (%s) %s)' % (v, e)
def make_app(e1, e2):    return '(%s %s)' % (e1, e2)
def make_let(v, e1, e2): return '(let ((%s %s)) %s)' % (v, e1, e2)

eof        = match(r'$')
_          = match(r'\s*')
identifier = match(r'([A-Za-z_]\w*)\s*')

def test1():
    V     = identifier
    E     = delay(lambda: 
            V                        >> make_var
          | '\\' +_+ V + '.' +_+ E   >> make_lam
          | '(' +_+ E + E + ')' +_   >> make_app)
    start = _+ E #+ eof
    return lambda s: start(s)[0]

## test1()('x y')
#. 'x'
## test1()(r'\x.x')
#. '(lambda (x) x)'
## test1()('(x   x)')
#. '(x x)'


def test2(string):
    V     = identifier
    F     = delay(lambda: 
            V                                     >> make_var
          | '\\' +_+ V.plus() + hug + '.' +_+ E   >> fold_lam
          | '(' +_+ E + ')' +_)
    E     = F + F.star()                          >> fold_app
    start = _+ E

    vals = start.attempt(string)
    return vals and vals[0]

def fold_app(f, *fs): return reduce(make_app, fs, f)
def fold_lam(vp, e): return foldr(make_lam, e, vp)

def foldr(f, z, xs):
    for x in reversed(xs):
        z = f(x, z)
    return z

## test2('x')
#. 'x'
## test2('\\x.x')
#. '(lambda (x) x)'
## test2('(x x)')
#. '(x x)'

## test2('hello')
#. 'hello'
## test2(' x')
#. 'x'
## test2('\\x . y  ')
#. '(lambda (x) y)'
## test2('((hello world))')
#. '(hello world)'

## test2('  hello ')
#. 'hello'
## test2('hello     there hi')
#. '((hello there) hi)'
## test2('a b c d e')
#. '((((a b) c) d) e)'

## test2('')
## test2('x x . y')
#. '(x x)'
## test2('\\.x')
## test2('(when (in the)')
## test2('((when (in the)))')
#. '(when (in the))'

## test2('\\a.a')
#. '(lambda (a) a)'

## test2('  \\hello . (hello)x \t')
#. '(lambda (hello) (hello x))'

## test2('\\M . (\\f . M (f f)) (\\f . M (f f))')
#. '(lambda (M) ((lambda (f) (M (f f))) (lambda (f) (M (f f)))))'

## test2('\\a b.a')
#. '(lambda (a) (lambda (b) a))'

## test2('\\a b c . a b')
#. '(lambda (a) (lambda (b) (lambda (c) (a b))))'


# Smoke test: grammars

## exceptionally(lambda: Grammar(r"a = . b = a. a = .")())
#. GrammarError('Multiply-defined rules: a',)

## exceptionally(lambda: Grammar(r"a = b|c|d. c = .")())
#. GrammarError('Undefined rules: b, d',)

## exceptionally(lambda: Grammar(r"a = ")())
#. GrammarError('Bad grammar', ('a = ', ''))

pushy = Grammar(r"""
main: :'x'.
""")()
## pushy.main('')
#. ('x',)

nums = Grammar(r"""
# This is a comment.
main : nums !/./.  # So's this.
nums : num ** ','.
num  : /([0-9]+)/ :int.
""")()
sum_nums = lambda s: sum(nums.main(s))

## sum_nums('10,30,43')
#. 83
## nums.nums('10,30,43')
#. (10, 30, 43)
## nums.nums('')
#. ()
## nums.num('10,30,43')
#. (10,)

## nums.main('10,30,43')
#. (10, 30, 43)
## nums.main.attempt('10,30,43 xxx')


gsub_grammar = Grammar(r"""
gsub = [:p :replace | /(.)/]*.
""")
def gsub(text, p, replacement):
    g = gsub_grammar(p=p, replace=lambda: replacement)
    return ''.join(g.gsub(text))
## gsub('hi there WHEEWHEE to you WHEEEE', 'WHEE', 'GLARG')
#. 'hi there GLARGGLARG to you GLARGEE'


def catch_position(parse, string):
    try: parse(string)
    except Unparsable, e:
        print e.position

## catch_position(Grammar(r" 'x'* /$/ ")(), 'xxxhi')
#. 3


# Like test2, but in the grammar syntax and using immediate actions
# instead of folds:
test3_grammar = Grammar(r"""
start: FNORD E.
E:     F (F :make_app)*.
F:     V :make_var
    |  '\\' Lam
    |  '(' E ')'.
Lam:   V ('.' E | Lam) :make_lam.
V:     /([A-Za-z]+)/.
FNORD ~: /\s*/.
""")
test3 = test3_grammar(**globals()).start.expecting_one_result()

# Same checks as test2:

## test3('x')
#. 'x'
## test3('\\x.x')
#. '(lambda (x) x)'
## test3('(x x)')
#. '(x x)'

## test3('hello')
#. 'hello'
## test3(' x')
#. 'x'
## test3('\\x . y  ')
#. '(lambda (x) y)'
## test3('((hello world))')
#. '(hello world)'

## test3('  hello ')
#. 'hello'
## test3('hello     there hi')
#. '((hello there) hi)'
## test3('a b c d e')
#. '((((a b) c) d) e)'

## test3.attempt('')
## test3('x x . y')
#. '(x x)'
## test3.attempt('\\.x')
## test3.attempt('(when (in the)')
## test3('((when (in the)))')
#. '(when (in the))'

## test3('\\a.a')
#. '(lambda (a) a)'

## test3('  \\hello . (hello)x \t')
#. '(lambda (hello) (hello x))'

## test3('\\M . (\\f . M (f f)) (\\f . M (f f))')
#. '(lambda (M) ((lambda (f) (M (f f))) (lambda (f) (M (f f)))))'

## test3('\\a b.a')
#. '(lambda (a) (lambda (b) a))'

## test3('\\a b c . a b')
#. '(lambda (a) (lambda (b) (lambda (c) (a b))))'
