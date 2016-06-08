"""
Parser adapted from github.com/darius/pother as an example and for testing.
"""

from parson import Grammar

def make_var(v):        return v
def make_const(c):      return c
def make_lam(v, e):     return '(lambda (%s) %s)' % (v, e)
def make_app(e1, e2):   return '(%s %s)' % (e1, e2)
def make_send(e1, e2):  return '(%s <- %s)' % (e1, e2)
def make_lit_sym(v):    return '(quote %s)' % v

def make_let(decls, e):
    return '(let %s %s)' % (' '.join(decls), e)

def make_defer(v):      return '(defer %s)' % v
def make_bind(v, e):    return '(bind %s %s)' % (v, e)
def make_eqn(vs, e):
    assert isinstance(vs, tuple)
    assert isinstance(e, str), "hey %r" % (e,)
    return '((%s) %s)' % (' '.join(vs), e)

def make_list_pattern(*params):
    return '(list %s)' % ' '.join(map(str, params))

def make_list_expr(es):
    return '(list %s)' % ' '.join(map(str, es))

def make_case(e, cases): return ('(case %s %s)'
                                 % (e, ' '.join('(%s %s)' % pair
                                                for pair in cases)))

def foldr(f, z, xs):
    for x in reversed(xs):
        z = f(x, z)
    return z

def fold_app(f, fs):  return reduce(make_app, fs, f)
def fold_apps(fs):    return reduce(make_app, fs)
def fold_send(f, fs): return reduce(make_send, fs, f)
def fold_lam(vp, e):  return foldr(make_lam, e, vp)

# XXX not sure about paramlist here:
fold_infix_app = lambda _left, _op, _right: \
    fold_app(_op, [fold_apps(_left), _right])

# XXX & was \ for lambda

# XXX
#                         [Param,operator,_,Param,  
#                          lambda _left,_op,_right: [_op, _left, _right]]

toy_grammar = Grammar(r"""
main       :  '' E :end.

E          :  Fp '`' V '`' E     :fold_infix_app
           |  Fp                 :fold_apps
           |  '&' Vp '=>' E      :fold_lam
           |  "let" Decls E      :make_let
           |  "case" E Cases     :make_case.

Cases      :  Case+ :hug.
Case       :  '|' Param '=>' E   :hug.

Param      :  Const
           |  V
           |  '(' Param ')'
           |  '[' ParamList ']'.

ParamList  :  Param ',' Param    :make_list_pattern.

Decls      :  Decl+ :hug.
Decl       :  "defer" V ';'      :make_defer
           |  "bind" V '=' E ';' :make_bind
           |  Vp '=' E ';'       :make_eqn.

Fp         :  F+ :hug.
F          :  Const              :make_const
           |  V                  :make_var
           |  '(' E ')'
           |  '{' F Fp '}'       :fold_send
           |  '[' E ** (',') ']' :hug :make_list_expr.

Vp         :  V+ :hug.
V          :  Identifier
           |  Operator.

Identifier :  /(?!let\b|case\b|defer\b|bind\b)([A-Za-z_]\w*)\b/.
Operator   :  /(<=|:=|[!+-.])/.

Const      :  '.' V               :make_lit_sym
           |  /"([^"]*)"/         :repr
           |  /(-?\d+)/
           |  '(' ')'            :'()'
           |  '[' ']'            :'[]'.

FNORD     ~:  /\s*/.
""")(**globals())

## toy_grammar.main('.+')
#. ('(quote +)',)
## toy_grammar.main('0 .+')
#. ('(0 (quote +))',)

## print toy_grammar.main('0')
#. ('0',)
## print toy_grammar.main('x')
#. ('x',)
## print toy_grammar.main('let x=y; x')[0]
#. (let ((x) y) x)
## print toy_grammar.main.attempt('')
#. None
## print toy_grammar.main('x x . y')[0]
#. ((x x) (quote y))
## print toy_grammar.main.attempt('(when (in the)')
#. None
## print toy_grammar.main('&M => (&f => M (f f)) (&f => M (f f))')[0]
#. (lambda (M) ((lambda (f) (M (f f))) (lambda (f) (M (f f)))))
## print toy_grammar.main('&a b c => a b')[0]
#. (lambda (a) (lambda (b) (lambda (c) (a b))))

## toy_grammar.main('x')
#. ('x',)
## toy_grammar.main('let x=y; x')
#. ('(let ((x) y) x)',)
## toy_grammar.main.attempt('')
## toy_grammar.main('x x . y')
#. ('((x x) (quote y))',)
## toy_grammar.main.attempt('(when (in the)')
## toy_grammar.main('&M => (&f => M (f f)) (&f => M (f f))')
#. ('(lambda (M) ((lambda (f) (M (f f))) (lambda (f) (M (f f)))))',)
## toy_grammar.main('&a b c => a b')
#. ('(lambda (a) (lambda (b) (lambda (c) (a b))))',)

mint = r"""
let make_mint name =
    case make_brand name
      | [sealer, unsealer] =>

        let defer mint;
            real_mint name msg = case msg

              | .__print_on => &out => out .print (name .. "'s mint")

              | .make_purse => &initial_balance =>
                  (let _ = assert (is_int initial_balance);
                       _ = assert (0 .<= initial_balance);
                       balance = make_box initial_balance;
                       decr amount = (let _ = assert (is_int amount);
                                          _ = assert ((0 .<= amount) 
                                                      .and (amount .<= balance));
                                      balance .:= (balance .! .- amount));
                       purse msg = case msg
                         | .__print_on => &out =>
                             out .print ("has " .. (to_str balance)
                                                .. name .. " bucks")
                         | .balance  => balance .!
                         | .sprout   => mint .make_purse 0
                         | .get_decr => sealer .seal decr
                         | .deposit  => &amount source =>
                             (let _ = unsealer .unseal (source .get_decr) amount;
                              balance .:= (balance .! .+ amount));
                   purse);

            bind mint = real_mint;
        mint;

make_mint
"""
#try: print toy_grammar.main(mint)
#except Unparsable, e:
#    print e.args[1][0]
#    print 'XXX'
#    print e.args[1][1]
#print toy_grammar.main('let defer mint; mint')
## print toy_grammar.main(mint)[0]
#. (let ((make_mint name) (case (make_brand name) ((list sealer unsealer) (let (defer mint) ((real_mint name msg) (case msg ((quote __print_on) (lambda (out) ((out (quote print)) ((name (quote .)) "'s mint")))) ((quote make_purse) (lambda (initial_balance) (let ((_) (assert (is_int initial_balance))) ((_) (assert ((0 (quote <=)) initial_balance))) ((balance) (make_box initial_balance)) ((decr amount) (let ((_) (assert (is_int amount))) ((_) (assert ((((0 (quote <=)) amount) (quote and)) ((amount (quote <=)) balance)))) ((balance (quote :=)) (((balance (quote !)) (quote -)) amount)))) ((purse msg) (case msg ((quote __print_on) (lambda (out) ((out (quote print)) (((((('has ' (quote .)) (to_str balance)) (quote .)) name) (quote .)) ' bucks')))) ((quote balance) (balance (quote !))) ((quote sprout) ((mint (quote make_purse)) 0)) ((quote get_decr) ((sealer (quote seal)) decr)) ((quote deposit) (lambda (amount) (lambda (source) (let ((_) (((unsealer (quote unseal)) (source (quote get_decr))) amount)) ((balance (quote :=)) (((balance (quote !)) (quote +)) amount)))))))) purse))))) (bind mint real_mint) mint)))) make_mint)

mintskel = r"""
let make_mint name =
    case make_brand name
      | [sealer, unsealer] =>

        let defer mint;
        mint;

make_mint
"""
## print toy_grammar.main(mintskel)[0]
#. (let ((make_mint name) (case (make_brand name) ((list sealer unsealer) (let (defer mint) mint)))) make_mint)

voting = r"""
let make_one_shot f =
        let armed = make_box True;
        &x => let _ = assert (armed .! .not);
                  _ = armed .:= False;
        f x;
    
    start_voting voters choices timer =
        let ballot_box = map (&_ => make_box 0) choices;
            poll voter =
                let make_checkbox pair = 
                        case pair
                          | [choice, tally] =>
                            [choice, make_one_shot (&_ => 
                                       tally .:= (tally .! .+ 1))];
                    ballot = map make_checkbox (zip choices ballot_box);
                {voter ballot};
            _ = for_each poll voters;
        [close_polls, totals];

start_voting
"""
## print toy_grammar.main(voting)[0]
#. (let ((make_one_shot f) (let ((armed) (make_box True)) (lambda (x) (let ((_) (assert ((armed (quote !)) (quote not)))) ((_) ((armed (quote :=)) False)) (f x))))) ((start_voting voters choices timer) (let ((ballot_box) ((map (lambda (_) (make_box 0))) choices)) ((poll voter) (let ((make_checkbox pair) (case pair ((list choice tally) (list (((choice ,) make_one_shot) (lambda (_) ((tally (quote :=)) (((tally (quote !)) (quote +)) 1)))))))) ((ballot) ((map make_checkbox) ((zip choices) ballot_box))) (voter <- ballot))) ((_) ((for_each poll) voters)) (list ((close_polls ,) totals)))) start_voting)
