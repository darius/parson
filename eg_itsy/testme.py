"""
Halp tests.
"""

from itsy import parser
from c_emitter import c_emit, c_exp

def cdef(string):
    t, = parser.top(string)
    return c_emit(t)

def cdefs(string):
    for x in parser.top(string):
        print c_emit(x) + '\n'

p1 = 'let b: [5]int;'
## cdef(p1)
#. 'int b[5];'

p2 = 'let b: [5]^int;'
## cdef(p2)
#. 'int *b[5];'

p3 = 'let b: [8][1]int;'
## cdef(p3)
#. 'int b[8][1];'

## cdef('to f(): void {}')
#. 'void f(void) {\n    \n}'

p4 = 'let a: int = (1, 2, 3);'
## cdef(p4)
#. 'int a = (1, 2, 3);'

p5 = 'let a: int = a^++^;'
## cdef(p5)
#. 'int a = *(*a)++;'

# I guess this output without parens is actually correct, though confusing to read. TODO check
# Maybe we should just always parenthesize a run of ',' operators...
p6, = parser.statement('return if pattern < pp && pp[-1] == c {--pp, 1} else {0};')
## c_emit(p6)
#. 'return pattern < pp && pp[-1] == c ? --pp, 1 : 0;'

p7, = parser.exp('a || b || c')
## c_exp(p7, 0)
#. 'a || b || c'

## cdef('let a: ^int;')
#. 'int *a;'
## cdef('let a: ^^int;')
#. 'int **a;'
## cdef('let f: ^()int;')
#. 'int (*f)(void);'
## cdef('to f(): ^int {}')
#. 'int *f(void) {\n    \n}'
## cdef('let f: ^()^int;')
#. 'int *(*f)(void);'
## cdef('let f: ^()void;')
#. 'void (*f)(void);'
## cdef('to g(): ^()void {return f;}')
#. 'void (*g(void))(void) {\n    return f;\n}'
## cdef('to f(h: ^()void): ^()void {}')
#. 'void (*f(void (*h)(void)))(void) {\n    \n}'
## cdef('let f: ^(^()void) ^()void;')
#. 'void (*(*f)(void (*)(void)))(void);'
## cdef('let api: []^int = [NULL];')
#. 'int *api[] = {\n    NULL,\n};'
## cdef('let pai: ^[10]int;')
#. 'int (*pai)[10];'

## cdef('let a: ^[3]^[5]int;')
#. 'int (*(*a)[3])[5];'

## cdef('typedef a = ^b;')
#. 'typedef b *a;'
## cdef('typedef VTable = [5]^()int;')
#. 'typedef int (*VTable[5])(void);'

## print cdef('struct A { x, y: int; }')
#. struct A {
#.     int x;
#.     int y;
#. }

ce, = parser.exp('([1,2]): []int')
## print c_exp(ce)
#. (int []) {
#.     1,
#.     2,
#. }

with open('eg/examples.itsy') as f: examples = f.read()
## cdefs(examples)
#. int a = 5;
#. 
#. int f(int x) {
#.     return x * x;
#. }
#. 
#. int fib(int n) {
#.     return n < 2 ? 1 : fib(n - 1) + fib(n - 2);
#. }
#. 
#. int fact(int n) {
#.     int p = 1;
#.     for (; 0 < n; --n) {
#.         p *= n;
#.     }
#.     return p;
#. }
#. 
#. void asm_store_field(Address address, int L, int R, Cell cell) {
#.     assert(address < memory_size);
#.     if (VERBOSE) {
#.         int temp[12];
#.         unparse_cell(temp, cell);
#.         printf("%4o(%u,%u): %s\n", address, L, R, temp);
#.     }
#.     memory[address] = set_field(cell, make_field_spec(L, R), memory[address]);
#. }
#. 
#. int make16(uint8 a, uint8 b) {
#.     return (int) a + ((int) b << 8);
#. }
#. 

with open('eg/regex.itsy') as f: regex = f.read()
## cdefs(regex)
#. enum {
#.     loud = 0,
#. };
#. 
#. void error(char *plaint) {
#.     fprintf(stderr, "%s\n", plaint);
#.     exit(1);
#. }
#. 
#. enum {
#.     max_insns = 8192,
#.     accept = 0,
#. };
#. 
#. enum {
#.     op_accept,
#.     op_eat,
#.     op_fork,
#.     op_loop,
#. };
#. 
#. int ninsns;
#. 
#. uint8 accepts[max_insns];
#. uint8 ops[max_insns];
#. 
#. int16 arg1[max_insns];
#. int16 arg2[max_insns];
#. 
#. char *names[4] = {
#.     "win",
#.     "eat",
#.     "fork",
#.     "loop",
#. };
#. 
#. void dump1(int pc) {
#.     printf("%c %2u: %-4s ", accepts[pc] ? '*' : ' ', pc, names[ops[pc]]);
#.     printf(pc == accept ? "\n" : ops[pc] == op_eat ? "'%c' %d\n" : "%d %d\n", arg1[pc], arg2[pc]);
#. }
#. 
#. void dump(void) {
#.     int pc;
#.     for (pc = ninsns - 1; 0 <= pc; --pc) {
#.         dump1(pc);
#.     }
#. }
#. 
#. uint8 occupied[max_insns];
#. 
#. void after(char ch, int start, int end, int **next_states) {
#.     while (start != end) {
#.         int r = arg1[start];
#.         int s = arg2[start];
#.         switch (ops[start]) {
#.             case op_eat: {
#.                 if (r == ch && !occupied[s]) {
#.                     *(*next_states)++ = s;
#.                     occupied[s] = 1;
#.                 }
#.                 return;
#.             } break;
#.             case op_fork: {
#.                 after(ch, r, end, next_states);
#.                 start = s;
#.             } break;
#.             case op_loop: {
#.                 after(ch, r, start, next_states);
#.                 start = s;
#.             } break;
#.             default: {
#.                 error("Can't happen");
#.             } break;
#.         }
#.     }
#. }
#. 
#. int states0[max_insns];
#. int states1[max_insns];
#. 
#. int run(int start, char *input) {
#.     if (accepts[start]) {
#.         return 1;
#.     }
#.     int *cur_start;
#.     int *cur_end;
#.     int *next_start;
#.     int *next_end;
#.     cur_start = states0, cur_end = cur_start;
#.     next_start = states1, next_end = next_start;
#.     *cur_end++ = start;
#.     memset(occupied, 0, ninsns);
#.     for (; *input; ++input) {
#.         int *state;
#.         for (state = cur_start; state < cur_end; ++state) {
#.             after(*input, *state, accept, &next_end);
#.         }
#.         for (state = next_start; state < next_end; ++state) {
#.             if (accepts[*state]) {
#.                 return 1;
#.             }
#.             occupied[*state] = 0;
#.         }
#.         int *t = cur_start;
#.         cur_start = next_start, cur_end = next_end;
#.         next_start = next_end = t;
#.     }
#.     return 0;
#. }
#. 
#. int emit(uint8 op, int r, int s, uint8 accepting) {
#.     if (max_insns <= ninsns) {
#.         error("Pattern too long");
#.     }
#.     ops[ninsns] = op, arg1[ninsns] = r, arg2[ninsns] = s;
#.     accepts[ninsns] = accepting;
#.     return ninsns++;
#. }
#. 
#. char *pattern;
#. char *pp;
#. 
#. int eat(char c) {
#.     return pattern < pp && pp[-1] == c ? --pp, 1 : 0;
#. }
#. 
#. int parsing(int precedence, int state) {
#.     int rhs;
#.     if (pattern == pp || pp[-1] == '(' || pp[-1] == '|') {
#.         rhs = state;
#.     } else if (eat(')')) {
#.         rhs = parsing(0, state);
#.         if (!eat('(')) {
#.             error("Mismatched ')'");
#.         }
#.     } else if (eat('*')) {
#.         rhs = emit(op_loop, 0, state, accepts[state]);
#.         arg1[rhs] = parsing(6, rhs);
#.     } else {
#.         rhs = emit(op_eat, *--pp, state, 0);
#.     }
#.     while (pattern < pp && pp[-1] != '(') {
#.         int prec = pp[-1] == '|' ? 3 : 5;
#.         if (prec <= precedence) {
#.             break;
#.         }
#.         if (eat('|')) {
#.             int rhs2 = parsing(prec, state);
#.             rhs = emit(op_fork, rhs, rhs2, accepts[rhs] || accepts[rhs2]);
#.         } else {
#.             rhs = parsing(prec, rhs);
#.         }
#.     }
#.     return rhs;
#. }
#. 
#. int parse(char *string) {
#.     pattern = string;
#.     pp = pattern + strlen(pattern);
#.     ninsns = 0;
#.     int state = parsing(0, emit(op_accept, 0, 0, 1));
#.     if (pattern != pp) {
#.         error("Bad pattern");
#.     }
#.     return state;
#. }
#. 
#. int main(int argc, char **argv) {
#.     if (argc != 2) {
#.         error("Usage: grep pattern");
#.     }
#.     int start_state = parse(argv[1]);
#.     if (loud) {
#.         printf("start: %u\n", start_state);
#.         dump();
#.     }
#.     int matched = 0;
#.     char line[9999];
#.     while (fgets(line, sizeof line, stdin)) {
#.         if (run(start_state, line)) {
#.             fputs(line, stdout);
#.             matched = 1;
#.         }
#.     }
#.     return !matched;
#. }
#. 
