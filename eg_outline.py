"""
Parse an outline using indentation.
After Higher Order Perl, section 8.6.
"""

import parson as P

def swallow(fn):
    return P._Peg('swallow',
                  lambda s, far, (i, vals): fn(*vals).run(s, far, (i, ())))

def Node(margin):
    return P.seclude(P.match(r'( {%d,})' % margin)
                     + swallow(lambda indent:
                               (line + Node(len(indent)+1).star()) >> P.hug))

line = '* ' + P.match(r'(.*)\n?')

outline = Node(0).star() + ~P.match(r'.')


eg = """\
* Hello
  * Aloha
    * Bonjour
    * Adieu
  * also
* Whatever
  * yay?"""

## from pprint import pprint; pprint(outline(eg))
#. (('Hello', ('Aloha', ('Bonjour',), ('Adieu',)), ('also',)),
#.  ('Whatever', ('yay?',)))
