"""
Convert from roman numeral to int.
"""

from parson import Grammar

g = Grammar(r"""
numeral = digit+ !/./.
digit = 'CM' :'900' | 'M' :'1000'
      | 'CD' :'400' | 'D'  :'500'
      | 'XC'  :'90' | 'C'  :'100'
      | 'XL'  :'40' | 'L'   :'50'
      | 'IX'   :'9' | 'X'   :'10'
      | 'IV'   :'4' | 'V'    :'5'
                    | 'I'    :'1'.
""")()

def int_from_roman(string):
    return sum(map(int, g.numeral(string.strip())))

## int_from_roman('MCMLXXIX')
#. 1979
