"""
Word-count function.
"""

from parson import match, feed

blanks = match(r'\s*')
marks  = match(r'\S+')
zero   = feed(lambda:   0)
add1   = feed(lambda n: n+1)

wc     = zero + blanks + (add1 + marks + blanks).star()

example_input = r"""  hi  there   hey
how are you?
  fine.

thanks.

ok then."""

## wc(example_input)
#. (10,)
