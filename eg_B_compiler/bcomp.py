"""
Tie the modules together into a compiler.
"""

import sys

import ast
from gen_vm_asm import gen_program
from parson import Grammar, Unparsable

with open('b2020.parson') as f:
    grammar_source = f.read()
parser = Grammar(grammar_source).bind(ast)

## parser.constant(r"""42 """)
#. (Literal('42', 'decimal'),)
## parser.constant(r"""042 """)
#. (Literal('042', 'octal'),)
## parser.constant(r"""'he' """)
#. (Literal("'he'", 'char'),)
## parser.constant(r"""'\n\n' """)
#. (Literal("'\\n\\n'", 'char'),)

## parser.exp(r"x=5")
#. (Assign(Variable('x'), '=', Literal('5', 'decimal')),)

eg0 = 'printn() {}'
## parser.program(eg0)
#. (Proc('printn', (), Block(())),)
decls0 = parser.program(eg0)
## gen_program(decls0)
#. printn	proc
#. 	params
#. 	return_void
#. 	endproc
#. 

eg1 = r"""
    /* The following function will print a non-negative number, n, to
      the base b, where 2<=b<=10,  This routine uses the fact that
      in the ANSCII character set, the digits O to 9 have sequential
      code values.  */

    printn(n,b) {
    	extern putchar;
    	auto a;

    	if(a=n/b) /* assignment, not test for equality */
    		printn(a, b); /* recursive */
    	putchar(n%b + '0');
    }
"""
decls1 = parser.program(eg1)
## decls1
#. (Proc('printn', ('n', 'b'), Block((Extern(('putchar',)), Auto((('a', None),)), If_stmt(Assign(Variable('a'), '=', Binary_exp(Variable('n'), '/', Variable('b'))), Exp(Call(Variable('printn'), (Variable('a'), Variable('b')))), None), Exp(Call(Variable('putchar'), (Binary_exp(Binary_exp(Variable('n'), '%', Variable('b')), '+', Literal("'0'", 'char')),)))))),)

## gen_program(decls1)
#. printn	proc
#. 	params	n, b
#. putchar	extern
#. a	local
#. 	addr	a
#. 	value	n
#. 	value	b
#. 	op2	/
#. 	assign	=
#. 	if_not	endif.0
#. 	value	printn
#. 	value	a
#. 	value	b
#. 	call	2
#. 	pop
#. endif.0
#. 	value	putchar
#. 	value	n
#. 	value	b
#. 	op2	%
#. 	push	'0'
#. 	op2	+
#. 	call	1
#. 	pop
#. 	return_void
#. 	endproc
#. 

eg2 = r"""
/* The following program will calculate the constant e-2 to about
   4000 decimal digits, and print it 50 characters to the line in
   groups of 5 characters.  The method is simple output conversion
   of the expansion
     1/2! + 1/3! + ... = .111....
   where the bases of the digits are 2, 3, 4, . . . */

main() {
	extern putchar, n, v;
	auto i, c, col, a;

	i = col = 0;
	while(i<n)
		v[i++] = 1;
	while(col<2*n) {
		a = n+1 ;
		c = i = 0;
		while (i<n) {
			c += v[i] *10;
			v[i++]  = c%a;
			c /= a--;
		}

		putchar(c+'0');
		if(!(++col%5))
			putchar(col%50?' ': '\n');
	}
	putchar('\n\n');
}

v[2000];
n = 2000;
"""
decls2 = parser.program(eg2)
## decls2
#. (Proc('main', (), Block((Extern(('putchar', 'n', 'v')), Auto((('i', None), ('c', None), ('col', None), ('a', None))), Exp(Assign(Variable('i'), '=', Assign(Variable('col'), '=', Literal('0', 'decimal')))), While(Binary_exp(Variable('i'), '<', Variable('n')), Exp(Assign(Unary_exp('*', Binary_exp(Variable('v'), '+', Post_incr(Variable('i'), '++'))), '=', Literal('1', 'decimal')))), While(Binary_exp(Variable('col'), '<', Binary_exp(Literal('2', 'decimal'), '*', Variable('n'))), Block((Exp(Assign(Variable('a'), '=', Binary_exp(Variable('n'), '+', Literal('1', 'decimal')))), Exp(Assign(Variable('c'), '=', Assign(Variable('i'), '=', Literal('0', 'decimal')))), While(Binary_exp(Variable('i'), '<', Variable('n')), Block((Exp(Assign(Variable('c'), '+=', Binary_exp(Unary_exp('*', Binary_exp(Variable('v'), '+', Variable('i'))), '*', Literal('10', 'decimal')))), Exp(Assign(Unary_exp('*', Binary_exp(Variable('v'), '+', Post_incr(Variable('i'), '++'))), '=', Binary_exp(Variable('c'), '%', Variable('a')))), Exp(Assign(Variable('c'), '/=', Post_incr(Variable('a'), '--')))))), Exp(Call(Variable('putchar'), (Binary_exp(Variable('c'), '+', Literal("'0'", 'char')),))), If_stmt(Unary_exp('!', Binary_exp(Pre_incr('++', Variable('col')), '%', Literal('5', 'decimal'))), Exp(Call(Variable('putchar'), (If_exp(Binary_exp(Variable('col'), '%', Literal('50', 'decimal')), Literal("' '", 'char'), Literal("'\\n'", 'char')),))), None)))), Exp(Call(Variable('putchar'), (Literal("'\\n\\n'", 'char'),)))))), Global('v', Literal('2000', 'decimal'), None), Global('n', None, (Literal('2000', 'decimal'),)))

## gen_program(decls2)
#. main	proc
#. 	params
#. putchar	extern
#. n	extern
#. v	extern
#. i	local
#. c	local
#. col	local
#. a	local
#. 	addr	i
#. 	addr	col
#. 	push	0
#. 	assign	=
#. 	assign	=
#. 	pop
#. 	jump	while.1
#. loop.2
#. 	value	v
#. 	addr	i
#. 	postinc	++
#. 	op2	+
#. 	push	1
#. 	assign	=
#. 	pop
#. while.1
#. 	value	i
#. 	value	n
#. 	op2	<
#. 	if	loop.2
#. 	jump	while.3
#. loop.4
#. 	addr	a
#. 	value	n
#. 	push	1
#. 	op2	+
#. 	assign	=
#. 	pop
#. 	addr	c
#. 	addr	i
#. 	push	0
#. 	assign	=
#. 	assign	=
#. 	pop
#. 	jump	while.5
#. loop.6
#. 	addr	c
#. 	value	v
#. 	value	i
#. 	op2	+
#. 	op1	*
#. 	push	10
#. 	op2	*
#. 	assign	+=
#. 	pop
#. 	value	v
#. 	addr	i
#. 	postinc	++
#. 	op2	+
#. 	value	c
#. 	value	a
#. 	op2	%
#. 	assign	=
#. 	pop
#. 	addr	c
#. 	addr	a
#. 	postinc	--
#. 	assign	/=
#. 	pop
#. while.5
#. 	value	i
#. 	value	n
#. 	op2	<
#. 	if	loop.6
#. 	value	putchar
#. 	value	c
#. 	push	'0'
#. 	op2	+
#. 	call	1
#. 	pop
#. 	addr	col
#. 	preinc	++
#. 	push	5
#. 	op2	%
#. 	op1	!
#. 	if_not	endif.7
#. 	value	putchar
#. 	value	col
#. 	push	50
#. 	op2	%
#. 	if_not	else.8
#. 	push	' '
#. 	jump	endif.9
#. else.8
#. 	push	'\n'
#. endif.9
#. 	call	1
#. 	pop
#. endif.7
#. while.3
#. 	value	col
#. 	push	2
#. 	value	n
#. 	op2	*
#. 	op2	<
#. 	if	loop.4
#. 	value	putchar
#. 	push	'\n\n'
#. 	call	1
#. 	pop
#. 	return_void
#. 	endproc
#. 
#. v	global	size(2000)
#. 
#. n	global	init(2000)
#. 

eg3 = r"""
printf(fmt, x1,x2,x3,x4,x5,x6,x7,x8,x9) {
	extern printn, char, putchar;
	auto adx, x, c, i, j;

	i= 0;
	adx = &x1;
loop :
	while((c=char(fmt,i++) ) != '%') {
		if(c == '\e')
			return;
		putchar(c);
	}
	x = *adx++;
	switch c = char(fmt,i++) {

	case 'd':
	case 'o':
		if(x < 0) {
			x = -x ;
			putchar('-');
		}
		printn(x, c=='o'?8:10);
		goto loop;

	case 'c' : /* char */
		putchar(x);
		goto loop;

	case 's': /* string */
		while((c=char(x, j++)) != '\e')
			putchar(c);
		goto loop;
	}
	putchar('%') ;
	i--;
	adx--;
	goto loop;
}
"""
decls3 = parser.program(eg3)
## decls3
#. (Proc('printf', ('fmt', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9'), Block((Extern(('printn', 'char', 'putchar')), Auto((('adx', None), ('x', None), ('c', None), ('i', None), ('j', None))), Exp(Assign(Variable('i'), '=', Literal('0', 'decimal'))), Exp(Assign(Variable('adx'), '=', Address_of(Variable('x1')))), Label('loop', While(Binary_exp(Assign(Variable('c'), '=', Call(Variable('char'), (Variable('fmt'), Post_incr(Variable('i'), '++')))), '!=', Literal("'%'", 'char')), Block((If_stmt(Binary_exp(Variable('c'), '==', Literal("'\\e'", 'char')), Return(None), None), Exp(Call(Variable('putchar'), (Variable('c'),))))))), Exp(Assign(Variable('x'), '=', Unary_exp('*', Post_incr(Variable('adx'), '++')))), Switch(Assign(Variable('c'), '=', Call(Variable('char'), (Variable('fmt'), Post_incr(Variable('i'), '++')))), Block((Case(Literal("'d'", 'char'), Case(Literal("'o'", 'char'), If_stmt(Binary_exp(Variable('x'), '<', Literal('0', 'decimal')), Block((Exp(Assign(Variable('x'), '=', Unary_exp('-', Variable('x')))), Exp(Call(Variable('putchar'), (Literal("'-'", 'char'),))))), None))), Exp(Call(Variable('printn'), (Variable('x'), If_exp(Binary_exp(Variable('c'), '==', Literal("'o'", 'char')), Literal('8', 'decimal'), Literal('10', 'decimal'))))), Goto(Variable('loop')), Case(Literal("'c'", 'char'), Exp(Call(Variable('putchar'), (Variable('x'),)))), Goto(Variable('loop')), Case(Literal("'s'", 'char'), While(Binary_exp(Assign(Variable('c'), '=', Call(Variable('char'), (Variable('x'), Post_incr(Variable('j'), '++')))), '!=', Literal("'\\e'", 'char')), Exp(Call(Variable('putchar'), (Variable('c'),))))), Goto(Variable('loop'))))), Exp(Call(Variable('putchar'), (Literal("'%'", 'char'),))), Exp(Post_incr(Variable('i'), '--')), Exp(Post_incr(Variable('adx'), '--')), Goto(Variable('loop'))))),)

## gen_program(decls3)
#. printf	proc
#. 	params	fmt, x1, x2, x3, x4, x5, x6, x7, x8, x9
#. printn	extern
#. char	extern
#. putchar	extern
#. adx	local
#. x	local
#. c	local
#. i	local
#. j	local
#. 	addr	i
#. 	push	0
#. 	assign	=
#. 	pop
#. 	addr	adx
#. 	addr	x1
#. 	assign	=
#. 	pop
#. loop
#. 	jump	while.10
#. loop.11
#. 	value	c
#. 	push	'\e'
#. 	op2	==
#. 	if_not	endif.12
#. 	return_void
#. endif.12
#. 	value	putchar
#. 	value	c
#. 	call	1
#. 	pop
#. while.10
#. 	addr	c
#. 	value	char
#. 	value	fmt
#. 	addr	i
#. 	postinc	++
#. 	call	2
#. 	assign	=
#. 	push	'%'
#. 	op2	!=
#. 	if	loop.11
#. 	addr	x
#. 	addr	adx
#. 	postinc	++
#. 	op1	*
#. 	assign	=
#. 	pop
#. 	addr	c
#. 	value	char
#. 	value	fmt
#. 	addr	i
#. 	postinc	++
#. 	call	2
#. 	assign	=
#. 	switch
#. 	case	'd', case.13
#. 	case	'o', case.14
#. 	case	'c', case.15
#. 	case	's', case.16
#. 	endcases
#. case.13			# 'd'
#. case.14			# 'o'
#. 	value	x
#. 	push	0
#. 	op2	<
#. 	if_not	endif.17
#. 	addr	x
#. 	value	x
#. 	op1	-
#. 	assign	=
#. 	pop
#. 	value	putchar
#. 	push	'-'
#. 	call	1
#. 	pop
#. endif.17
#. 	value	printn
#. 	value	x
#. 	value	c
#. 	push	'o'
#. 	op2	==
#. 	if_not	else.18
#. 	push	8
#. 	jump	endif.19
#. else.18
#. 	push	10
#. endif.19
#. 	call	2
#. 	pop
#. 	value	loop
#. 	goto
#. case.15			# 'c'
#. 	value	putchar
#. 	value	x
#. 	call	1
#. 	pop
#. 	value	loop
#. 	goto
#. case.16			# 's'
#. 	jump	while.20
#. loop.21
#. 	value	putchar
#. 	value	c
#. 	call	1
#. 	pop
#. while.20
#. 	addr	c
#. 	value	char
#. 	value	x
#. 	addr	j
#. 	postinc	++
#. 	call	2
#. 	assign	=
#. 	push	'\e'
#. 	op2	!=
#. 	if	loop.21
#. 	value	loop
#. 	goto
#. 	value	putchar
#. 	push	'%'
#. 	call	1
#. 	pop
#. 	addr	i
#. 	postinc	--
#. 	pop
#. 	addr	adx
#. 	postinc	--
#. 	pop
#. 	value	loop
#. 	goto
#. 	return_void
#. 	endproc
#. 
