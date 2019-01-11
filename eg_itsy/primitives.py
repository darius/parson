"""
Built-in global definitions
"""

from ast import Int_type, Float_type

prims = {}

prims['int8']    = Int_type(1, 'i')
prims['int16']   = Int_type(2, 'i')
prims['int32']   = Int_type(4, 'i')
prims['int64']   = Int_type(8, 'i')

prims['uint8']   = Int_type(1, 'u')
prims['uint16']  = Int_type(2, 'u')
prims['uint32']  = Int_type(4, 'u')
prims['uint64']  = Int_type(8, 'u')

prims['float32'] = Float_type(4)
prims['float64'] = Float_type(8)

# XXX platform-dependent; make configurable or something
# XXX check that these match my C compiler's defs
prims['bool']    = prims['uint8'] 
prims['char']    = prims['int8'] 
prims['int']     = prims['int64'] 
prims['uint']    = prims['uint64']
prims['size_t']  = prims['uint64']

#prims['true']    = XXX

# TODO: defs from c_prelude.h
