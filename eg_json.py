"""
Example: parse JSON.
"""

from parson import Grammar

literals = dict(true=True,
                false=False,
                null=None)
mk_literal = literals.get

mk_object  = lambda *pairs: dict(pairs)
escape     = lambda s: s.decode('unicode-escape')
mk_number  = float

# Following http://www.json.org/
json_parse = Grammar(r"""
start     :  _ value.

object    :  '{'_ pairs? '}'_         :mk_object.
pairs     :  pair (','_ pair)*.
pair      :  string ':'_ value        :hug.

array     :  '['_ elements? ']'_      :hug.
elements  :  value (','_ value)*.

value     :  string | number
          |  object | array
          |  /(true|false|null)\b/_   :mk_literal.

string    :  '"' char* '"'_           :join.
char      :  /([^\x00-\x1f"\\])/
          |  /\\(["\/\\])/
          |  /(\\[bfnrt])/            :escape
          |  /(\\u)/ xd xd xd xd      :join :escape.
xd        :  /([0-9a-fA-F])/.

number    :  int (frac exp? | exp)? _ :join :mk_number.
int       :  /(-?0)/ ~/\d/
          |  /(-?[1-9]\d*)/.
frac      :  /([.]\d+)/.
exp       :  /([eE][+-]?\d+)/.

_         :  /\s*/.
""")(**globals()).start

# XXX The spec says "whitespace may be inserted between any pair of
# tokens, but leaves open just what's a token. So is the '-' in '-1' a
# token? Should I allow whitespace there?

## json_parse('[1,1]')
#. ((1.0, 1.0),)
## json_parse('true')
#. (True,)
## json_parse(r'"hey \b\n \u01ab o hai"')
#. (u'hey \x08\n \u01ab o hai',)
## json_parse('{"hey": true}')
#. ({'hey': True},)
## json_parse('[{"hey": true}]')
#. (({'hey': True},),)
## json_parse('[{"hey": true}, [-12.34]]')
#. (({'hey': True}, (-12.34,)),)
## json_parse('0')
#. (0.0,)
## json_parse('0.125e-2')
#. (0.00125,)

## json_parse.attempt( '0377')
## json_parse.attempt('{"hi"]')

# Udacity CS212 problem 3.1:

## json_parse('["testing", 1, 2, 3]')
#. (('testing', 1.0, 2.0, 3.0),)

## json_parse('-123.456e+789')
#. (-inf,)

## json_parse('{"age": 21, "state":"CO","occupation":"rides the rodeo"}')
#. ({'age': 21.0, 'state': 'CO', 'occupation': 'rides the rodeo'},)
