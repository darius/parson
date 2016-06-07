"""
Convert from roman numeral to int.
"""

from parson import Grammar

g = Grammar(r"""
numeral = digit+ :end.
digit = 'CM'  :'900' | 'CD' :'400' | 'XC'  :'90' | 'XL' :'40' | 'IX'  :'9' | 'IV' :'4'
      |  'M' :'1000' |  'D' :'500' |  'C' :'100' |  'L' :'50' |  'X' :'10' |  'V' :'5' | 'I' :'1'.
""")()

def int_from_roman(string):
    return sum(map(int, g.numeral(string.strip())))

## int_from_roman('MCMLXXIX')
#. 1979
