"""
Word-count function.
"""

from parson import match, feed

blanks = match(r'\s*')
marks  = match(r'\S+')
zero   = feed(lambda:   0)
add1   = feed(lambda n: n+1)

wc     = zero + blanks + (add1 + marks + blanks).star()

## wc('  ')
#. (0,)
## wc('a b c ')
#. (3,)
## wc(example_input)
#. (10,)

example_input = r"""  hi  there   hey
how are you?
  fine.

thanks.

ok then."""
