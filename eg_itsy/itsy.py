"""
Tie the modules together and try them out.
"""

from parson import Grammar
import itsy_ast

with open('itsy.parson') as f:
    grammar_source = f.read()
grammar = Grammar(grammar_source)
parse = grammar.bind(itsy_ast)

program = parse.top('let a: int = 5; to f(x: int): int { return x * x; }')

## program
#. (Let('a', Int(), Literal(5)), To('f', (('x', Int()),), Int(), Block((), (Return(Binary_exp(Variable('x'), '*', Variable('x'))),))))
## program[0].c()
#. 'int a = 5;'
## print program[1].c()
#. int f(int x) {
#.   return (x * x);
#. }

p1 = parse.top('let b: int[5];')[0]
## p1.c()
#. 'int b[5];'

p2 = parse.top('let b: int[5]@;')[0]
## p2.c()
#. 'int (*b)[5];'

p3 = parse.top('let b: int[8][1];')[0]
## p3.c()
#. 'int b[8][1];'

## parse.top('to f(): void {}')[0].c()
#. 'void f(void) {\n  \n}'

with open('itsy.examples') as f:
    examples = f.read()

## for x in parse.top(examples): print x.c() + '\n'
#. int a = 5;
#. 
#. int f(int x) {
#.   return (x * x);
#. }
#. 
#. int fib(int n) {
#.   return ((n < 2) ? 1 : (fib((n - 1)) + fib((n - 2))));
#. }
#. 
#. int fact(int n) {
#.   int p = 1;
#.   for(; (0 < n); --(n)) {
#.     (p *= n);
#.   }
#.   return p;
#. }
#. 
#. void asm_store_field(Address address, int L, int R, Cell cell) {
#.   assert((address < memory_size));
#.   if (VERBOSE) {
#.     int temp[12];
#.     unparse_cell(temp, cell);
#.     printf("%4o(%u,%u): %s\n", address, L, R, temp);
#.   }
#.   (memory[address] = set_field(cell, make_field_spec(L, R), memory[address]));
#. }
#. 

with open('regex.itsy') as f:
    regex = f.read()
## for x in parse.top(regex): print x.c() + '\n'
#. enum constant {
#.   loud = 0,
#. }
#. 
#. void error(char (*plaint)) {
#.   
#. }
#. 
