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
command   :  /(\d+)/_ :int /(.*)/        /$/ :set_line
          |  'run'  /\b/_                /$/ :run
          |  'new'  /\b/_                /$/ :new
          |  'load' /\b/_ /(\S+)/_       /$/ :load
          |  'save' /\b/_ /(\S+)/_       /$/ :save
          |  stmt
          |                              /$/.

stmt      :  'print'  /\b/_ printing                  /$/        :next
          |  '?'          _ printing                  /$/        :next
          |  'input'  /\b/_ id                        /$/ :input :next
          |  'goto'   /\b/_ exp0                      /$/        :goto
          |  'if'     /\b/_ relexp 'then' /\b/_ exp0  /$/        :if_goto
          |  'gosub'  /\b/_ exp0                      /$/        :gosub
          |  'return' /\b/_                           /$/        :return_
          |  'end'    /\b/_                           /$/        :end
          |  'list'   /\b/_                           /$/ :list  :next
          |  'rem'    /\b/   /.*/                     /$/        :next
          | ('let'    /\b/_)? id '='_ exp0            /$/ :store :next.

printing  :  (display writes)?.
writes    :  ';'_        printing
          |  ','_ :space printing
          |       :newline.
display   :  exp0 :write
          |  '"' [qchar :write]* '"'_.
qchar     :  /"(")/
          |  /([^"])/.

relexp    :  exp0 (  '<>'_ exp0 :ne
                   | '<='_ exp0 :le
                   | '<' _ exp0 :lt
                   | '=' _ exp0 :eq
                   | '>='_ exp0 :ge
                   | '>' _ exp0 :gt
                  )?.
exp0      :  exp1 (  '+'_ exp1 :add
                   | '-'_ exp1 :sub
                  )*.
exp1      :  exp2 (  '*'_ exp2 :mul
                   | '/'_ exp2 :idiv
                  )*.
exp2      :  primary ('^'_ exp2 :pow)?.

primary   :  '-'_ exp1 :neg
          |  /(\d+)/_  :int
          |  id        :fetch
          |  '('_ exp0 ')'_.

id        :  /([a-z])/_.  # TODO: longer names, screening out reserved words
_         :  /\s*/.
""")


lines = []      # A sorted array of (line_number, source_line) pairs.
pc = None       # The program counter: an index into lines[], or None.
return_stack = []     # A stack of line numbers of GOSUBs in progress.
env = {}

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
    return alter(lambda *args: (fn(*args), ())[1]) # XXX kinda ugh

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
