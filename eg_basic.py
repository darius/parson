"""
BASIC interpreter, inspired by Tiny BASIC.
"""

import bisect, operator, sys
from parson import Grammar, alter

def chat():
    print "I am Puny Basic. Enter 'bye' to dismiss me."
    while True:
        try: text = raw_input('> ').strip()
        except EOFError: break
        if text == 'bye': break
        try: basic.command(text)
        except Exception as e:
            # TODO: put the current line# in the prompt instead, if any;
            #  should work nicely with a resumable STOP statement
            print e, ('' if pc is None else 'at line %d' % lines[pc][0])

grammar = Grammar(r"""
command   :  /(\d+)/ :int /(.*)/          /$/ :set_line
          |  "run"                        /$/ :run
          |  "new"                        /$/ :new
          |  "load"   /(\S+)/             /$/ :load
          |  "save"   /(\S+)/             /$/ :save
          |  stmt
          |                               /$/.

stmt      :  "print"  printing            /$/        :next
          |  '?'      printing            /$/        :next
          |  "input"  id                  /$/ :input :next
          |  "goto"   exp                 /$/        :goto
          |  "if"     relexp "then" exp   /$/        :if_goto
          |  "gosub"  exp                 /$/        :gosub
          |  "return"                     /$/        :return_
          |  "end"                        /$/        :end
          |  "list"                       /$/ :list  :next
          |  "rem"    /.*/                /$/        :next
          |  "let"?   id '=' exp          /$/ :store :next.

printing  :  (display writes)?.
writes    :  ';'        printing
          |  ',' :space printing
          |      :newline.

display  ~:  exp :write
          |  '"' [qchar :write]* '"' FNORD.
qchar    ~:  /"(")/
          |  /([^"])/.

relexp    :  exp  (  '<>' exp :ne
                   | '<=' exp :le
                   | '<'  exp :lt
                   | '='  exp :eq
                   | '>=' exp :ge
                   | '>'  exp :gt
                  )?.
exp       :  exp1 (  '+' exp1 :add
                   | '-' exp1 :sub
                  )*.
exp1      :  exp2 (  '*' exp2 :mul
                   | '/' exp2 :idiv
                  )*.
exp2      :  primary ('^' exp2 :pow)?.

primary   :  '-' exp1 :neg
          |  /(\d+)/  :int
          |  id       :fetch
          |  '(' exp ')'.

id        :  /([a-z])/.  # TODO: longer names, screening out reserved words

FNORD    ~:  /\s*/.
""")


lines = []         # A sorted array of (line_number, source_line) pairs.
pc = None          # The program counter: an index into lines[], or None.
return_stack = []  # A stack of line numbers of GOSUBs in progress.
env = {}           # Curent variable values.

def run():
    reset()
    go()

def reset():
    global pc
    pc = 0 if lines else None
    return_stack[:] = []
    env.clear()

def go():
    global pc
    while pc is not None:       # TODO: check for stopped, instead
        _, line = lines[pc]
        pc, = basic.stmt(line)

def new():
    lines[:] = []
    reset()

def load(filename):
    f = open(filename)
    new()
    with f:
        for line in f:
            basic.command(line)

def save(filename):
    with open(filename, 'w') as f:
        for pair in lines:
            f.write('%d %s\n' % pair)

def listing():
    for n, line in lines:
        print n, line

def find(n):
    i = bisect.bisect(lines, (n, ''))
    return slice(i, i+1 if i < len(lines) and lines[i][0] == n else i)

def set_line(n, text):
    lines[find(n)] = [(n, text)] if text else []

def goto(n):
    sl = find(n)
    if sl.start == sl.stop: raise Exception("Missing line", n)
    return sl.start

def if_goto(flag, n):
    return goto(n) if flag else next_line(pc)

def next_line(a_pc):
    return None if a_pc in (None, len(lines)-1) else a_pc+1

def gosub(n):
    target = goto(n)
    return_stack.append(lines[pc][0])
    return target

def return_():
    return next_line(goto(return_stack.pop()))


def nullify(fn):
    def nullified(*args):
        fn(*args)
        return ()
    return alter(nullified)

basic = grammar(
    fetch    = env.__getitem__,
    store    = nullify(env.__setitem__),
    input    = nullify(lambda var: env.__setitem__(var, int(raw_input()))),
    set_line = nullify(set_line),
    goto     = goto,
    if_goto  = if_goto,
    gosub    = gosub,
    return_  = return_,
    eq       = operator.eq,
    ne       = operator.ne,
    lt       = operator.lt,
    le       = operator.le,
    ge       = operator.ge,
    gt       = operator.gt,
    add      = operator.add,
    sub      = operator.sub,
    mul      = operator.mul,
    idiv     = operator.idiv,
    pow      = operator.pow,
    neg      = operator.neg,
    end      = lambda: None,
    list     = nullify(listing),
    run      = nullify(run),
    next     = lambda: next_line(pc),
    new      = nullify(new),
    load     = nullify(load),
    save     = nullify(save),
    write    = nullify(lambda x: sys.stdout.write(str(x))),
    space    = nullify(lambda: sys.stdout.write(' ')),
    newline  = nullify(lambda: sys.stdout.write('\n')),
)


if __name__ == '__main__':
    chat()
    
## basic.command('100 print "hello"')
#. ()
## lines
#. [(100, 'print "hello"')]
## basic.command('100 print "goodbye"')
#. ()
## lines
#. [(100, 'print "goodbye"')]
## basic.command('99 print 42,')
#. ()
## lines
#. [(99, 'print 42,'), (100, 'print "goodbye"')]

## basic.command('run')
#. 42 goodbye
#. ()


## basic.command('print')
#. (None,)
## basic.command('let x = 5')
#. (None,)
## basic.command('print x*x')
#. 25
#. (None,)
## basic.command('print 2+2; -5, "hi"')
#. 4-5 hi
#. (None,)
## basic.command('? 42 * (5-3) + -2^2')
#. 80
#. (None,)
## basic.command('print 2^3^2, ')
#. 512 
#. (None,)
## basic.command('print 5-3-1')
#. 1
#. (None,)
## basic.command('print 3/2')
#. 1
#. (None,)

## basic.command('new')
#. ()
## basic.command('load countdown.bas')
#. ()
## basic.command('list')
#. 10 let a = 10
#. 20 if a < 0 then 60
#. 30 print a
#. 40 let a = a - 1
#. 50 goto 20
#. 60 print "Blast off!"
#. 70 end
#. (None,)
## basic.command('run')
#. 10
#. 9
#. 8
#. 7
#. 6
#. 5
#. 4
#. 3
#. 2
#. 1
#. 0
#. Blast off!
#. ()
