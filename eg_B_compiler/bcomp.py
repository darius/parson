"""
Tie the modules together into a compiler.
"""

import sys

import ast
from gen_vm_asm import gen_program, gen_global_decl
from parson import Grammar, Unparsable

with open('b2020.parson') as f:
    grammar_source = f.read()
parser = Grammar(grammar_source).bind(ast)

## parser.constant(r"""42 """)
#. (Literal('42', 'decimal'),)
## parser.constant(r"""042 """)
#. (Literal('042', 'octal'),)
## parser.constant(r"""'he' """)
#. (Literal('he', 'char'),)
## parser.constant(r"""'\n\n' """)
#. (Literal('\n\n', 'char'),)

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
#. (Proc('printn', ('n', 'b'), Block((Extern(('putchar',)), Auto((('a', None),)), If_stmt(Assign(Variable('a'), '=', Binary_exp(Variable('n'), '/', Variable('b'))), Exp(Call(Variable('printn'), (Variable('a'), Variable('b')))), None), Exp(Call(Variable('putchar'), (Binary_exp(Binary_exp(Variable('n'), '%', Variable('b')), '+', Literal('0', 'char')),)))))),)

## gen_program(decls1)
#. printn	proc
#. 	params	n, b
#. putchar	extern
#. a	local	None
#. 	addr	a
#. 	value	n
#. 	value	b
#. 	op2	/
#. 	assign	=
#. 	if_not	_endif_0
#. 	value	printn
#. 	value	a
#. 	value	b
#. 	call	2
#. 	pop
#. _endif_0
#. 	value	putchar
#. 	value	n
#. 	value	b
#. 	op2	%
#. 	push	char('0')
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
#. (Proc('main', (), Block((Extern(('putchar', 'n', 'v')), Auto((('i', None), ('c', None), ('col', None), ('a', None))), Exp(Assign(Variable('i'), '=', Assign(Variable('col'), '=', Literal('0', 'decimal')))), While(Binary_exp(Variable('i'), '<', Variable('n')), Exp(Assign(Index(Variable('v'), Post_incr(Variable('i'), '++')), '=', Literal('1', 'decimal')))), While(Binary_exp(Variable('col'), '<', Binary_exp(Literal('2', 'decimal'), '*', Variable('n'))), Block((Exp(Assign(Variable('a'), '=', Binary_exp(Variable('n'), '+', Literal('1', 'decimal')))), Exp(Assign(Variable('c'), '=', Assign(Variable('i'), '=', Literal('0', 'decimal')))), While(Binary_exp(Variable('i'), '<', Variable('n')), Block((Exp(Assign(Variable('c'), '+=', Binary_exp(Index(Variable('v'), Variable('i')), '*', Literal('10', 'decimal')))), Exp(Assign(Index(Variable('v'), Post_incr(Variable('i'), '++')), '=', Binary_exp(Variable('c'), '%', Variable('a')))), Exp(Assign(Variable('c'), '/=', Post_incr(Variable('a'), '--')))))), Exp(Call(Variable('putchar'), (Binary_exp(Variable('c'), '+', Literal('0', 'char')),))), If_stmt(Unary_exp('!', Binary_exp(Pre_incr('++', Variable('col')), '%', Literal('5', 'decimal'))), Exp(Call(Variable('putchar'), (If_exp(Binary_exp(Variable('col'), '%', Literal('50', 'decimal')), Literal(' ', 'char'), Literal('\n', 'char')),))), None)))), Exp(Call(Variable('putchar'), (Literal('\n\n', 'char'),)))))), Global('v', Literal('2000', 'decimal'), None), Global('n', None, (Literal('2000', 'decimal'),)))

## gen_program(decls2)
#. main	proc
#. 	params
#. putchar	extern
#. n	extern
#. v	extern
#. i	local	None
#. c	local	None
#. col	local	None
#. a	local	None
#. 	addr	i
#. 	addr	col
#. 	push	decimal('0')
#. 	assign	=
#. 	assign	=
#. 	pop
#. 	jump	_while_1
#. _loop_2
#. 	value	v
#. 	addr	i
#. 	postinc	++
#. 	op2	+
#. 	push	decimal('1')
#. 	assign	=
#. 	pop
#. _while_1
#. 	value	i
#. 	value	n
#. 	op2	<
#. 	if	_loop_2
#. 	jump	_while_3
#. _loop_4
#. 	addr	a
#. 	value	n
#. 	push	decimal('1')
#. 	op2	+
#. 	assign	=
#. 	pop
#. 	addr	c
#. 	addr	i
#. 	push	decimal('0')
#. 	assign	=
#. 	assign	=
#. 	pop
#. 	jump	_while_5
#. _loop_6
#. 	addr	c
#. 	value	v
#. 	value	i
#. 	op2	index
#. 	push	decimal('10')
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
#. _while_5
#. 	value	i
#. 	value	n
#. 	op2	<
#. 	if	_loop_6
#. 	value	putchar
#. 	value	c
#. 	push	char('0')
#. 	op2	+
#. 	call	1
#. 	pop
#. 	addr	col
#. 	preinc	++
#. 	push	decimal('5')
#. 	op2	%
#. 	op1	!
#. 	if_not	_endif_7
#. 	value	putchar
#. 	value	col
#. 	push	decimal('50')
#. 	op2	%
#. 	if_not	_else_8
#. 	push	char(' ')
#. 	jump	_endif_9
#. _else_8
#. 	push	char('\n')
#. _endif_9
#. 	call	1
#. 	pop
#. _endif_7
#. _while_3
#. 	value	col
#. 	push	decimal('2')
#. 	value	n
#. 	op2	*
#. 	op2	<
#. 	if	_loop_4
#. 	value	putchar
#. 	push	char('\n\n')
#. 	call	1
#. 	pop
#. 	return_void
#. 	endproc
#. 
#. v	global	size(decimal('2000'))
#. 
#. n	global	init(decimal('2000'))
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
#. (Proc('printf', ('fmt', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9'), Block((Extern(('printn', 'char', 'putchar')), Auto((('adx', None), ('x', None), ('c', None), ('i', None), ('j', None))), Exp(Assign(Variable('i'), '=', Literal('0', 'decimal'))), Exp(Assign(Variable('adx'), '=', Address_of(Variable('x1')))), Label('loop', While(Binary_exp(Assign(Variable('c'), '=', Call(Variable('char'), (Variable('fmt'), Post_incr(Variable('i'), '++')))), '!=', Literal('%', 'char')), Block((If_stmt(Binary_exp(Variable('c'), '==', Literal('\xff', 'char')), Return(None), None), Exp(Call(Variable('putchar'), (Variable('c'),))))))), Exp(Assign(Variable('x'), '=', Unary_exp('*', Post_incr(Variable('adx'), '++')))), Switch(Assign(Variable('c'), '=', Call(Variable('char'), (Variable('fmt'), Post_incr(Variable('i'), '++')))), Block((Case(Literal('d', 'char'), Case(Literal('o', 'char'), If_stmt(Binary_exp(Variable('x'), '<', Literal('0', 'decimal')), Block((Exp(Assign(Variable('x'), '=', Unary_exp('-', Variable('x')))), Exp(Call(Variable('putchar'), (Literal('-', 'char'),))))), None))), Exp(Call(Variable('printn'), (Variable('x'), If_exp(Binary_exp(Variable('c'), '==', Literal('o', 'char')), Literal('8', 'decimal'), Literal('10', 'decimal'))))), Goto(Variable('loop')), Case(Literal('c', 'char'), Exp(Call(Variable('putchar'), (Variable('x'),)))), Goto(Variable('loop')), Case(Literal('s', 'char'), While(Binary_exp(Assign(Variable('c'), '=', Call(Variable('char'), (Variable('x'), Post_incr(Variable('j'), '++')))), '!=', Literal('\xff', 'char')), Exp(Call(Variable('putchar'), (Variable('c'),))))), Goto(Variable('loop'))))), Exp(Call(Variable('putchar'), (Literal('%', 'char'),))), Exp(Post_incr(Variable('i'), '--')), Exp(Post_incr(Variable('adx'), '--')), Goto(Variable('loop'))))),)

## gen_program(decls3)
#. printf	proc
#. 	params	fmt, x1, x2, x3, x4, x5, x6, x7, x8, x9
#. printn	extern
#. char	extern
#. putchar	extern
#. adx	local	None
#. x	local	None
#. c	local	None
#. i	local	None
#. j	local	None
#. 	addr	i
#. 	push	decimal('0')
#. 	assign	=
#. 	pop
#. 	addr	adx
#. 	addr	x1
#. 	assign	=
#. 	pop
#. loop
#. 	jump	_while_10
#. _loop_11
#. 	value	c
#. 	push	char('\xff')
#. 	op2	==
#. 	if_not	_endif_12
#. 	return_void
#. _endif_12
#. 	value	putchar
#. 	value	c
#. 	call	1
#. 	pop
#. _while_10
#. 	addr	c
#. 	value	char
#. 	value	fmt
#. 	addr	i
#. 	postinc	++
#. 	call	2
#. 	assign	=
#. 	push	char('%')
#. 	op2	!=
#. 	if	_loop_11
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
#. 	case	char('d'), _case_13
#. 	case	char('o'), _case_14
#. 	case	char('c'), _case_15
#. 	case	char('s'), _case_16
#. 	endcases
#. _case_13			# char('d')
#. _case_14			# char('o')
#. 	value	x
#. 	push	decimal('0')
#. 	op2	<
#. 	if_not	_endif_17
#. 	addr	x
#. 	value	x
#. 	op1	-
#. 	assign	=
#. 	pop
#. 	value	putchar
#. 	push	char('-')
#. 	call	1
#. 	pop
#. _endif_17
#. 	value	printn
#. 	value	x
#. 	value	c
#. 	push	char('o')
#. 	op2	==
#. 	if_not	_else_18
#. 	push	decimal('8')
#. 	jump	_endif_19
#. _else_18
#. 	push	decimal('10')
#. _endif_19
#. 	call	2
#. 	pop
#. 	value	loop
#. 	goto
#. _case_15			# char('c')
#. 	value	putchar
#. 	value	x
#. 	call	1
#. 	pop
#. 	value	loop
#. 	goto
#. _case_16			# char('s')
#. 	jump	_while_20
#. _loop_21
#. 	value	putchar
#. 	value	c
#. 	call	1
#. 	pop
#. _while_20
#. 	addr	c
#. 	value	char
#. 	value	x
#. 	addr	j
#. 	postinc	++
#. 	call	2
#. 	assign	=
#. 	push	char('\xff')
#. 	op2	!=
#. 	if	_loop_21
#. 	value	loop
#. 	goto
#. 	value	putchar
#. 	push	char('%')
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
