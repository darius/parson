"""
Systems of linear equations over complex numbers, reimplementing a
hand-coded parser by Dave Long.
"""

from parson import Grammar

grammar = r"""  equations :end.

equations: equation ** ';'.

equation:  sum '=' sum                   :hug.
sum:       term ++ '+'                   :sum.
term:      number ('*' variable | :'')   :swap
         | variable [:'1' :complex]      :hug.
variable:  /([a-zA-Z]+)/ .
number:    ( (real ',' :'+')? real {'j'}
           | real )                      :join :complex.

real  ~: { '-'? /\d+/ ('.' /\d*/)? } FNORD.
FNORD ~: /\s*/.
"""
parse = Grammar(grammar)(sum=lambda *terms: dict((('',0j),) + terms),
                         swap=lambda x,y: (y,x))

examples = """\
		ht = 2j; wd = 1; sw = 0 
		ht = 2j; 2j*wd = ht; nw = 2j
		wd = 1; sw = 0; nw = 2j
		ne = 1,2j; sw = 0; 2j*wd = ht
		ne = 1,2j; nw = 2j; se = 1
		0.5*nw + 0.5*sw = 1j; nw = 2j; wd = 1
		0.5*nw + 0.5*sw = 1j; nw = 2j; wd = -0.5j*ht
""".splitlines()

def test():
    for s in examples:
        print s
        for lhs, rhs in parse(s):
            print '  ', lhs, '\t', '=', rhs

## test()
#. 		ht = 2j; wd = 1; sw = 0 
#.    {'': 0j, 'ht': (1+0j)} 	= {'': 2j}
#.    {'': 0j, 'wd': (1+0j)} 	= {'': (1+0j)}
#.    {'': 0j, 'sw': (1+0j)} 	= {'': 0j}
#. 		ht = 2j; 2j*wd = ht; nw = 2j
#.    {'': 0j, 'ht': (1+0j)} 	= {'': 2j}
#.    {'': 0j, 'wd': 2j} 	= {'': 0j, 'ht': (1+0j)}
#.    {'': 0j, 'nw': (1+0j)} 	= {'': 2j}
#. 		wd = 1; sw = 0; nw = 2j
#.    {'': 0j, 'wd': (1+0j)} 	= {'': (1+0j)}
#.    {'': 0j, 'sw': (1+0j)} 	= {'': 0j}
#.    {'': 0j, 'nw': (1+0j)} 	= {'': 2j}
#. 		ne = 1,2j; sw = 0; 2j*wd = ht
#.    {'': 0j, 'ne': (1+0j)} 	= {'': (1+2j)}
#.    {'': 0j, 'sw': (1+0j)} 	= {'': 0j}
#.    {'': 0j, 'wd': 2j} 	= {'': 0j, 'ht': (1+0j)}
#. 		ne = 1,2j; nw = 2j; se = 1
#.    {'': 0j, 'ne': (1+0j)} 	= {'': (1+2j)}
#.    {'': 0j, 'nw': (1+0j)} 	= {'': 2j}
#.    {'': 0j, 'se': (1+0j)} 	= {'': (1+0j)}
#. 		0.5*nw + 0.5*sw = 1j; nw = 2j; wd = 1
#.    {'': 0j, 'sw': (0.5+0j), 'nw': (0.5+0j)} 	= {'': 1j}
#.    {'': 0j, 'nw': (1+0j)} 	= {'': 2j}
#.    {'': 0j, 'wd': (1+0j)} 	= {'': (1+0j)}
#. 		0.5*nw + 0.5*sw = 1j; nw = 2j; wd = -0.5j*ht
#.    {'': 0j, 'sw': (0.5+0j), 'nw': (0.5+0j)} 	= {'': 1j}
#.    {'': 0j, 'nw': (1+0j)} 	= {'': 2j}
#.    {'': 0j, 'wd': (1+0j)} 	= {'': 0j, 'ht': -0.5j}
