"""
Based on https://www.w3.org/Addressing/URL/5_BNF.html
because I'm a lazy bastard; it's clearly not up to date
(as shown by 'right=wrong' below).
"""

from parson import Grammar

grammar = r"""  url :end.

url           : httpaddress | mailtoaddress.

mailtoaddress : {'mailto'} ':'   :'protocol'
                {(!'@' xalpha)+} :'user'
                '@' {hostname}   :'host'.

httpaddress   : {'http'} '://' :'protocol' hostport ('/' path)? ('?' search)? ('#' fragment)?.

hostport      : host (':' port)?.

host          : {hostname | hostnumber} :'host'.
hostname      : ialpha ('.' ialpha)*.
hostnumber    : digits '.' digits '.' digits '.' digits.

port          : {digits} :'port'.

path          : {(segment '/')* segment?} :'path'.
segment       : xpalpha+.

search        : {xalpha+ ('+' xalpha+)*}  :'search'.
fragment      : {xalpha+}                 :'fragment'.

xalpha        : alpha | digit | safe | extra | escape.
xpalpha       : xalpha | '+'.

ialpha        : alpha xalpha*.

alpha         : /[a-zA-Z]/.
digit         : /\d/.
digits        : /\d+/.
safe          : /[$_@.&+-]/.
extra         : /[!*"'(),]/.
escape        : '%' hex hex.
hex           : /[\dA-Fa-f]/.
"""
g = Grammar(grammar)()

## g.attempt('true')
## g('mailto:coyote@acme.com')
#. ('mailto', 'protocol', 'coyote', 'user', 'acme.com', 'host')
## g('http://google.com')
#. ('http', 'protocol', 'google.com', 'host')
## g.attempt('http://google.com//')
## g('http://en.wikipedia.org/wiki/Uniform_resource_locator')
#. ('http', 'protocol', 'en.wikipedia.org', 'host', 'wiki/Uniform_resource_locator', 'path')
## g.attempt('http://wry.me/fun/toys/yes.html?right=wrong#fraggle')
## g(        'http://wry.me/fun/toys/yes.html?rightwrong#fraggle')
#. ('http', 'protocol', 'wry.me', 'host', 'fun/toys/yes.html', 'path', 'rightwrong', 'search', 'fraggle', 'fragment')
