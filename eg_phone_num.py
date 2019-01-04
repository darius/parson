"""
The phone-number example at the top of
https://github.com/modernserf/little-language-lab
"""

from parson import Grammar

# const join = (...values) => values.join("")
# const phone = lang`
# Root      = ~("+"? "1" _)? AreaCode ~(_ "-"? _) Exchange ~(_ "-"? _) Line
#             ${(areaCode, exchange, line) => ({ areaCode, exchange, line })}
# AreaCode  = "(" _ (D D D ${join}) _ ")" ${(_, __, digits) => digits}
#           | D D D   ${join}
# Exchange  = D D D   ${join}
# Line      = D D D D ${join}
# D         = %digit
# _         = %whitespace*
# `
# phone.match("+1 (800) 555-1234")
# // { ok: true, value: { areaCode: "800", exchange: "555", line: "1234" } }


# Version 1: just gimme the data.

grammar1 = r"""
Root      : ('+'? '1' _)? AreaCode _ '-'? _ Exchange _ '-'? _ Line.
AreaCode  : '(' _ {D D D} _ ')'
          | {D D D}.
Exchange  : {D D D}.
Line      : {D D D D}.
D         = /\d/.
_         = /\s*/.
"""
g1 = Grammar(grammar1)()
## g1.Root("+1 (800) 555-1234")
#. ('800', '555', '1234')


# Version 2, returning a dict.
# We have to pass the dict constructor in as a semantic parameter, since
# Python lacks template strings.

grammar2 = r"""
Root      : ('+'? '1' _)? AreaCode _ '-'? _ Exchange _ '-'? _ Line :hug :dict.
AreaCode  : :'areaCode' ('(' _ {D D D} _ ')'
                        | {D D D}) :hug.
Exchange  : :'exchange' {D D D} :hug.
Line      : :'line' {D D D D} :hug.
D         = /\d/.
_         = /\s*/.
"""
parse_phone_number2 = Grammar(grammar2)(dict=dict).Root.expecting_one_result()
## parse_phone_number2("+1 (800) 555-1234")
#. {'areaCode': '800', 'line': '1234', 'exchange': '555'}


# Version 3, more my usual style.
# (Pass in semantic actions for the main productions
# and avoid the _ noise using a FNORD production.)

from structs import Struct

class PhoneNumber(Struct('area_code exchange line')):
    pass

grammar3 = r"""
Root        : /[+]?1/? AreaCode '-'? Exchange '-'? Line :PhoneNumber.
AreaCode    : '(' AreaDigits ')' | AreaDigits.

AreaDigits ~: /(\d\d\d)/.
Exchange   ~: /(\d\d\d)/.
Line       ~: /(\d\d\d\d)/.
FNORD      ~: /\s*/.
"""
g3 = Grammar(grammar3)(PhoneNumber=PhoneNumber)
parse_phone_number3 = g3.Root.expecting_one_result()
## parse_phone_number3("+1 (800) 555-1234")
#. PhoneNumber('800', '555', '1234')
