"""
A concatenative variant of John Backus's FP language.
http://en.wikipedia.org/wiki/FP_%28programming_language%29
"""

from parson import Grammar

program = {}

def FP(text):
    global program
    program = dict(primitives)
    program.update(fp_parse(text))

def mk_def(name, exp): return (name, exp)
def mk_call(name):     return lambda arg: program[name](arg)
def mk_if(c, t, e):    return lambda arg: (t if c(arg) else e)(arg)
def mk_compose(g, f):  return lambda arg: f(g(arg))
def mk_map(f):         return lambda arg: map(f, arg)
def mk_insertl(f):     return lambda arg: insertl(f, arg)
def mk_insertr(f):     return lambda arg: insertr(f, arg)
def mk_filter(f):      return lambda arg: filter(f, arg)
def mk_aref(n):        return (lambda arg: arg[n-1]) if 0 < n else (lambda arg: arg[n])
def mk_literal(n):     return lambda _: n
def mk_op(name):       return ops[name]
def mk_list(*exps):    return lambda arg: [f(arg) for f in exps]

escape = lambda s: s.decode('unicode-escape')

fp_parse = Grammar(r"""  def* :end.

def     : name '==' exp '.'      :mk_def.

exp     : term ('->' term ';' exp :mk_if)?.

term    : factor (term :mk_compose)?.

factor  : '@' factor             :mk_map
        | '/' factor             :mk_insertr
        | '\\' factor            :mk_insertl
        | '?' factor             :mk_filter
        | primary.

primary : integer                :mk_aref
        | '~' integer            :mk_literal
        | string                 :mk_literal
        | name                   :mk_call
        | /([<=>*+-])/~ !opchar FNORD
                                 :mk_op
        | '[' exp ** ',' ']'     :mk_list
        | '(' exp ')'.

opchar  : /[\w@\/\\?<=>*+-]/.

decimal : /(\d+)/                :int.
integer : /(-?\d+)/              :int.
name    : /([A-Za-z]\w*)/.

string ~: '"' schar* '"' FNORD   :join.
schar  ~: /([^\x00-\x1f"\\])/
        | /\\(["\\])/
        | /(\\[bfnrt])/          :escape.

FNORD  ~: /\s*/.

""")(**globals())

def insertl(f, xs):
    if not xs: return function_identity(f)
    return reduce(lambda x, y: f([x, y]), xs)

def insertr(f, xs):
    if not xs: return function_identity(f)
    z = xs[-1]
    for x in xs[-2::-1]:
        z = f([x, z])
    return z

add = lambda (x, y): x + y
sub = lambda (x, y): x - y
mul = lambda (x, y): x * y
div = lambda (x, y): x // y
mod = lambda (x, y): x % y
eq  = lambda (x, y): x == y
lt  = lambda (x, y): x < y
gt  = lambda (x, y): x > y

ops = {'+': add, '-': sub, '*': mul, '=': eq, '<': lt, '>': gt}

primitives = dict(
    apndl     = lambda (x, xs): [x] + xs,
    apndr     = lambda (xs, x): xs + [x],
    chain     = lambda lists: sum(lists, []),
    distl     = lambda (x, ys): [[x, y] for y in ys],
    distr     = lambda (xs, y): [[x, y] for x in xs],
    div       = div,
    enumerate = lambda xs: [(x, i) for i,x in enumerate(xs, 1)], # XXX unused
    id        = lambda x: x,
    iota      = lambda n: range(1, n+1),
    join      = lambda (strs, sep): sep.join(strs),
    length    = len,
    mod       = mod,
    rev       = lambda xs: xs[::-1],
    slice     = lambda (xs, n): [xs[:n-1], xs[n-1], xs[n:]],
    sort      = sorted,
    split     = lambda (s, sep): s.split(sep),
    tl        = lambda xs: xs[1:],
    transpose = lambda arg: zip(*arg),
)
primitives['and'] = lambda (x, y): x and y
primitives['or']  = lambda (x, y): x or y

def function_identity(f):
    if f in (add, sub): return 0
    if f in (mul, div): return 1
    # XXX could add chain, and, or, lt, gt, ...
    raise Exception("No known identity element", f)


examples = r"""
factorial == iota /*.

dot == transpose @* \+.
matmult == [1, 2 transpose] distr @distl @@dot.

iszero == [id, ~0] =.
divisible == mod iszero.
iseven == [id, ~2] divisible.

max == /(< -> 2; 1).

qsort == [length, ~2] < -> id; 
         [id, 1] distr [?< @1 qsort, ?= @1, ?> @1 qsort] chain.

euler1 == iota ?([[id, ~3] divisible, [id, ~5] divisible] or) /+.

fibs == [~40, 1] < -> tl; [[1,2] +, id] apndl fibs.
euler2 == [~2,~1] fibs ?iseven /+.

fibsr == [~40, -1] < -> rev tl rev; [id, [-1,-2] +] apndr fibsr.
euler2r == [~1,~2] fibsr ?iseven /+.
"""

def defs(names): return [program[name] for name in names.split()]

## FP(examples)
## factorial, dot, matmult = defs('factorial dot matmult')
## divisible, euler1 = defs('divisible euler1')
## qmax, qsort = defs('max qsort')
## qmax([1, 5, 3])
#. 5
## qmax([5, 1])
#. 5
## qsort([])
#. []
## qsort([3,1,4,1,5,9])
#. [1, 1, 3, 4, 5, 9]

## fibs, euler2, fibsr = defs('fibs euler2 fibsr')
## fibs([1,1])
#. [34, 21, 13, 8, 5, 3, 2, 1, 1]
## euler2(0)
#. 44
## fibsr([1,1])
#. [1, 1, 2, 3, 5, 8, 13, 21, 34]

## divisible([9, 5]), divisible([10, 5]), 
#. (False, True)
## euler1(9)
#. 23

## factorial(0)
#. 1
## factorial(5)
#. 120

## dot([[1,2], [3,4]])
#. 11
## dot([])
#. 0

## matmult([ [], [] ])
#. []
## matmult([ [[4]], [[5]] ])
#. [[20]]
## matmult([ [[2,0],[0,2]], [[5,6],[7,8]] ])
#. [[10, 12], [14, 16]]
## matmult([ [[0,1],[1,0]], [[5,6],[7,8]] ])
#. [[7, 8], [5, 6]]


# Inspired by James Morris, "Real programming in functional
# languages", figure 1.

kwic_program = r"""
kwic      == lines split  kwiclines  lines join.

kwiclines == @(words split generate) chain sort @2.
generate  == [id, length iota] distl @label.
label     == slice [2,
                    [1, [["<",2,">"] chars join], 3] chain  words join].

chars == [id, ""].
words == [id, " "].
lines == [id, "\n"].
"""

## FP(kwic_program)
## kwic, = defs('kwic')
## print kwic("leaves of grass\nflowers of evil")
#. flowers of <evil>
#. <flowers> of evil
#. leaves of <grass>
#. <leaves> of grass
#. flowers <of> evil
#. leaves <of> grass
