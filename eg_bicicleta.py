"""
Ported from https://github.com/darius/bicicleta.py/blob/master/core.py
Also uses https://github.com/darius/unreal/blob/master/structs.py
which is not in this repo.
"""

from structs import Struct
from parson import Grammar

class VarRef(Struct('name')):
    def __repr__(self):
        return self.name

class Literal(Struct('value')):
    def __repr__(self):
        return repr(self.value)

class Call(Struct('receiver slot')):
    def __repr__(self):
        return '%s.%s' % (self.receiver, self.slot)

class Extend(Struct('base name bindings')):
    def __repr__(self):
        return '%s{%s%s}' % ('' if self.base is empty_literal else self.base,
                             self.name + ': ' if self.name else '',
                               ', '.join('%s=%s' % binding
                                         for binding in self.bindings))

class SelflessExtend(Extend):
    pass

g = r"""      expr _ :end.

expr        : factor (infix_op factor       :mk_infix)*.
factor      : primary suffix*.

primary     : name                          :VarRef
            | _/(\d*\.\d+)/          :float :Literal
            | _/(\d+)/               :int   :Literal
            | _/"([^"\\]*)"/                :Literal
            | _'(' expr _')'
            | :empty extend.

suffix      = _'.' name                     :Call
            | extend
            | _'(' :'()' bindings _')'      :mk_funcall
            | _'[' :'[]' bindings _']'      :mk_funcall.

extend      = _'{' name _':' bindings _'}'  :Extend
            | _'{' :None     bindings _'}'  :SelflessExtend.
bindings    : binding ** bindsep            :name_positions.
bindsep     : newline | _','.
binding     : (name _'=' | :None) expr      :hug.

infix_op    : _ !lone_eq opchars.
opchars     : /([-~`!@$%^&*+<>?\/|\\=]+)/.
lone_eq     : '=' !opchars.

name        : _/([A-Za-z_][A-Za-z_0-9]*)/
            | _/'([^'\\]*)'/.

newline     : (!/\n/ blank)* /\n/.
blank       : /\s|#.*/.

_           : blank*.
"""

empty_literal = Literal('')   # XXX root_bob

def empty(): return empty_literal

def name_positions(*bindings):
    return tuple((('arg%d' % i if slot is None else slot), expr)
                 for i, (slot, expr) in enumerate(bindings, 1))

def mk_funcall(expr, slot, bindings):
    "  foo(x=y) ==> foo{x=y}.'()'  "
    return Call(SelflessExtend(expr, None, bindings), slot)

def mk_infix(left, operator, right):
    "   x + y ==> x.'+'(_=y)  "
    return mk_funcall(Call(left, operator), '()', (('arg1', right),))

parse = Grammar(g).bind(globals()).expecting_one_result()
# XXX .one_result()

## parse('5')
#. 5
## parse('{x: {y: {z: x ++ y{a="b"} <*> z.foo }}}')
#. {x: arg1={y: arg1={z: arg1=x.++{arg1=y{a='b'}}.().<*>{arg1=z.foo}.()}}}

## wtf = parse("{x=42, y=55}.x")
## wtf
#. {x=42, y=55}.x

## parse("137")
#. 137
## parse('137[yo="dude"]')
#. 137{yo='dude'}.[]

## adding = parse("137.'+' {arg1=1}.'()'")
## adding
#. 137.+{arg1=1}.()

## cmping = parse("(137 == 1).if(so=42, else=168)")
## cmping
#. 137.=={arg1=1}.().if{so=42, else=168}.()
## repr(cmping) == repr(parse("137.'=='{arg1=1}.'()'.if{so=42, else=168}.'()'"))
#. True

def make_fac(n):
    fac = parse("""
{env: 
 fac = {fac:   # fac for factorial
        '()' = (fac.n == 0).if(so = 1,
                               else = fac.n * env.fac(n = fac.n-1))}
}.fac(n=%d)""" % n)
    return fac

fac = make_fac(4)
## fac
#. {env: fac={fac: ()=fac.n.=={arg1=0}.().if{so=1, else=fac.n.*{arg1=env.fac{n=fac.n.-{arg1=1}.()}.()}.()}.()}}.fac{n=4}.()

def test():
    import glob
    for filename in glob.glob('*.bicicleta'):
        print filename
        with open(filename) as f:
            text = f.read()
        print parse(text)
        print

## test()
#. 2fib.bicicleta
#. {env: fib={fib: ()=fib.arg1.<{arg1=2}.().if{so=1, else=env.fib{arg1=fib.arg1.-{arg1=1}.()}.().+{arg1=env.fib{arg1=fib.arg1.-{arg1=2}.()}.()}.()}.()}}.fib{arg1=26}.()
#. 
#. fib.bicicleta
#. {env: fib={fib: arg1=3, n=fib.arg1, ()=fib.n.<{arg1=2}.().if{so=1, else=env.fib{arg1=fib.n.-{arg1=1}.()}.().+{arg1=env.fib{arg1=fib.n.-{arg1=2}.()}.()}.()}.()}}.fib{arg1=30}.()
#. 
#. freezer.bicicleta
#. {freezer: explanation=freezer.template.%{arg1=freezer}.(), template="<p>Thermal insulators in general conduct heat at\nabout {standard_insulator_conductivity} W/m/K.  Styrofoam is a better\ninsulator than some others; it conducts heat at about\n{styrofoam_conductivity} W/m/K.</p>\n\n<p>So let's consider building an icebox out of styrofoam.  The idea is\nthat you put in some ice from some other source every so often, and\nthat ice keeps the icebox cold.  If you salt the ice, it will melt\nbelow the freezing point of pure water, so your icebox can be a\nfreezer.</p>\n\n<p>{heat_flux_paragraph}</p>\n\n<p>{shape_paragraph}</p>\n\n<p>{less_stringent_shape_paragraph}</p>\n\n<p>{more_normal_temperature_paragraph}</p>\n", standard_insulator_conductivity=0.04, styrofoam_conductivity=0.033, insulator_conductivity=freezer.styrofoam_conductivity, heat_flux_paragraph="Suppose you want a {ice_kg} L of salted\nice in bottles to keep the temperature at {temp}\xc2\xb0C for {hours} hours\nat a time.  That means the total heat flux out has to be {ice_kg} L *\n{ice_heat_of_fusion} kcal/L over those {hours} hours, which is\n{heat_flux} kcal/h.  (That's {heat_flux_watts} watts.)".%{arg1=freezer}.(), ice_kg=2.0, temp=0.-{arg1=5}.(), hours=24, ice_heat_of_fusion=80, heat_flux=freezer.ice_kg.*{arg1=freezer.ice_heat_of_fusion}.()./{arg1=freezer.hours}.(), heat_flux_watts=freezer.heat_flux.*{arg1=freezer.kcalh_to_watts}.(), kcalh_to_watts=1.163, shape_paragraph="Suppose the interior of the freezer is\n{capacity} L in a convenient cubical shape; that's a {cube_side_cm}-cm\ncube, which has {area} m\xc2\xb2 of surface area to lose heat through.\nSuppose the outside air temperature is {outside_temp}\xc2\xb0C, for a\ndifference of {temp_gap} K.  {shape}".%{arg1=freezer}.(), shape='{insulator_conductivity} W/m/K * {area} m\xc2\xb2 * {temp_gap} K / \n{heat_flux_watts} W = {wall_thickness} m of wall thickness, for a\ntotal size of {total_size} m, cubed.'.%{arg1=freezer}.(), capacity=250.0, cube_side_cm=freezer.cuberoot{arg1=freezer.capacity./{arg1=1000}.()}.().*{arg1=100}.(), cuberoot={f: arg1=27.0, ()=f.arg1.**{arg1=1.0./{arg1=3}.()}.()}, area=freezer.cube_side_cm./{arg1=100}.().**{arg1=2}.().*{arg1=6}.(), outside_temp=35, temp_gap=freezer.outside_temp.-{arg1=freezer.temp}.(), wall_thickness=freezer.insulator_conductivity.*{arg1=freezer.area}.().*{arg1=freezer.temp_gap}.()./{arg1=freezer.heat_flux_watts}.(), total_size=freezer.cube_side_cm./{arg1=100}.().+{arg1=freezer.wall_thickness.*{arg1=2}.()}.(), less_stringent_shape_paragraph="That's unwieldy, so suppose\nyou're willing to use more ice. {less_stringent_heat_flux_paragraph}\n{less_stringent_shape}  That's {volume_ratio} times smaller.".%{arg1=freezer}.(), less_stringent_freezer=freezer{ice_kg=16.0}, less_stringent_shape=freezer.less_stringent_freezer.shape, less_stringent_heat_flux_paragraph=freezer.less_stringent_freezer.heat_flux_paragraph, volume_ratio=freezer.total_size.**{arg1=3}.()./{arg1=freezer.less_stringent_freezer.total_size.**{arg1=3}.()}.(), more_normal_temperature_paragraph='Suppose that the outside\ntemperature is only {more_normal_temperature}\xc2\xb0C on average.  Now, to\nmelt the same amount of ice per day, the walls of the icebox that\nmelts {ice_kg} kg of ice per day can be {thinner_walls} m thick, and\nthe walls of the smaller icebox that melts {less_stringent_ice_kg} kg\nof ice per day can be only {less_stringent_thinner_walls} m thick.\n\n'.%{arg1=freezer}.(), more_normal_temperature=23, in_more_normal_temperature=freezer{outside_temp=freezer.more_normal_temperature}, thinner_walls=freezer.in_more_normal_temperature.wall_thickness, less_stringent_ice_kg=freezer.less_stringent_freezer.ice_kg, less_stringent_thinner_walls=freezer.in_more_normal_temperature.less_stringent_freezer.wall_thickness}.explanation
#. 
#. sys.bicicleta
#. {empty={is_empty=sys.true, length=0, ++={appending: ()=appending.arg1}, foldr={folding: ()=folding.if_empty}, map={()=sys.empty}, repr='()', str='()'}, cons={list: is_empty=sys.false, length=1.+{arg1=list.rest.length}.(), ++={appending: ()=sys.cons{first=list.first, rest=list.rest.++{arg1=appending.arg1}.()}}, foldr={folding: ()=folding.if_cons{arg1=list.first, arg2=list.rest.foldr{if_empty=folding.if_empty, if_cons=folding.if_cons}.()}.()}, map={mapping: ()=sys.cons{first=mapping.arg1{arg1=list.first}.(), rest=list.rest.map{arg1=mapping.arg1}.()}}, repr='('.++{arg1=list.first.repr}.().++{arg1=':'}.().++{arg1=list.rest.repr}.().++{arg1=')'}.(), str='('.++{arg1=list.first.str}.().++{arg1=':'}.().++{arg1=list.rest.str}.().++{arg1=')'}.()}, vector={vec: elements=sys.cons{first=17, rest=sys.empty}, str=vec.repr, repr='['.++{arg1=vec.elements.repr}.().++{arg1=']'}.(), add_to={adding: n=adding.arg1, ()=adding.n.is_number.if{so=sys.vector{elements=vec.elements.map{arg1={each: ()=adding.n.+{arg1=each.arg1}.()}}.()}}.()}}}
#. 
#. sys_bool.bicicleta
#. {claim: not=claim.if{so=sys.false, else=sys.true}.(), &={doing: ()=claim.if{so=doing.arg1, else=sys.false}.()}, |={doing: ()=claim.if{so=sys.true, else=doing.arg1}.()}}
#. 
#. sys_number.bicicleta
#. {me: pred=me.-{arg1=1}.(), succ=me.+{arg1=1}.()}
#. 
#. sys_string.bicicleta
#. {string: %={subbing: ()=string.is_empty.if{so='', else=string.first.=={arg1='{'}.().if{so={chopping: result=subbing.arg1.reflective slot value{arg1=chopping.chopped.head}.().str.++{arg1=chopping.chopped.tail.%{arg1=subbing.arg1}.()}.(), chopped=chopping.chop{s=string.rest}.(), chop={scanning: ()=scanning.s.is_empty.if{so={head='', tail=''}, else=scanning.s.first.=={arg1='}'}.().if{so={head='', tail=scanning.s.rest}, else={whee: chop_rest=chopping.chop{s=scanning.s.rest}.(), head=scanning.s.first.++{arg1=whee.chop_rest.head}.(), tail=whee.chop_rest.tail}}.()}.()}}.result, else=string.first.++{arg1=string.rest.%{arg1=subbing.arg1}.()}.()}.()}.()}}
#. 
