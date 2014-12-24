"""
Translate from Zarf's Javascript (the subset used) to my Mutagen
grammar syntax.
http://www.eblong.com/zarf/mutagen/mutagen.js
"""

import re
from parson import Grammar, hug, join

def translate(grammar):
    for x, y in reversed(g.grammar(grammar)):
        print x, '=', y

g = Grammar(r"""
grammar = _ defn*.

defn :  var '='_ exp ';'_  :hug.

exp  :  'Choice'   args    :mk_choice
     |  'Fixed'    args    :mk_fixed
     |  'Sequence' args    :mk_sequence
     |  'Shuffle'  args    :mk_shuffle
     |  'Weighted' args    :mk_weighted
     |  /Period\b/_        :'.'
     |  /Comma\b/_         :','
     |  /Semicolon\b/_     :';'
     |  /Dash\b/_          :'--'
     |  /AAn\b/_           :'-a-an-'
     |  /Concat\b/_        :'-adjoining-'
     |  /null\b/_          :'()'
     |  var
     |  string
     |  int.

args :  '('_ exps? ')'_.
exps :  exp (','_ exps)*.

var  :  /([A-Za-z_]\w*)/_  :mk_var.

int  :  /(\d+)/            :mk_int.

string :  '"' qchar* '"'_  :join.
qchar  :  ~/["\\]/ /(.)/.

_       :  (space | comment)*.
space   :  /\s+/.
comment :  '/*' (~'*/' anyone)* '*/'.

anyone  :  /./ | /\n/.   # Ugh.
""")(hug = hug,
     join = join,

     mk_int = int,
     mk_var = lambda s: '-'+'-'.join(parse_camel(s))+'-',

     mk_choice   = lambda *xs: ' / '.join(xs),
     mk_fixed    = lambda tag, choice: '%s{ %s }' % (tag, choice),
     mk_sequence = lambda *xs: ' '.join(map(wrap, xs)),
     mk_shuffle  = lambda *xs: '{ %s }' % (' / '.join(xs)),
     mk_weighted = lambda *spairs: ' / '.join('[%s] %s' % (w, wrap(x))
                                              for w, x in zip(spairs[0::2],
                                                              spairs[1::2])),
     )

def wrap(x):
    return '(%s)' % x if ' / ' in x else x

def parse_camel(s):
    assert re.match(r'([A-Z][a-z]*)*$', s)
    return [part.lower() for part in re.findall(r'[A-Z][a-z]*', s)]

## parse_camel('HiThere')
#. ['hi', 'there']

## g.grammar('A = "hi";')
#. (('-a-', 'hi'),)
## g.grammar('A = Choice();')
#. (('-a-', ''),)
## g.grammar('A = Choice("hi");')
#. (('-a-', 'hi'),)
## g.grammar('A = Choice("hi", "there"); B = A;')
#. (('-a-', 'hi / there'), ('-b-', '-a-'))

## goreyfate = open('mutagen/goreyfate.js').read()
## translate(goreyfate)
#. -gorey-fate- = [2] -person-description- -action- -time- / [2] -time- -time-comma- -person-description- -action- / [1] it was -time- that -person-description- -action-
#. -action- = -passive-action- / -active-action-
#. -active-action- = -active-action-word- -active-action-prep- -a-an- ([1] -target-air- / [2] ()) ([1] -target-age- / [2] ()) -active-action-target-
#. -target-age- = old / moldering / aged / antiquated
#. -target-air- = disreputable / peculiar / mysterious / banal
#. -active-action-target- = altitude{ -active-action-target-hi- / -active-action-target-lo- }
#. -active-action-target-lo- = well / hole / cave / oubliette / cellar / pit
#. -active-action-target-hi- = tower / cliff / ruin / pillar / treehouse / garret
#. -active-action-prep- = altitude{ -active-action-prep-hi- / -active-action-prep-lo- }
#. -active-action-prep-lo- = down / into
#. -active-action-prep-hi- = down from / off / from
#. -active-action-word- = fell / tumbled / disappeared / plummeted / vanished / dropped
#. -passive-action- = -passive-action-word- ([2] -passive-action-qualifier- / [3] ())
#. -passive-action-qualifier- = away / at sea / without a trace / unexpectedly / mysteriously / into -action-result- / away into -action-result-
#. -action-result- = -dest-noun- / -dest-modifier- -dest-noun- / -a-an- -dest-noun- / -a-an- -dest-modifier- -dest-noun- / -a-an- -dest-form- of -dest-noun- / -a-an- -dest-form- of -dest-modifier- -dest-noun- / -a-an- -dest-modifier- -dest-form- of -dest-noun-
#. -dest-form- = solidity{ puddle / bucket / vat / heap / cloud / waft }
#. -dest-modifier- = noisome / pearlescent / foul / fetid / glittering / dark / briny / glistening / cloying
#. -dest-noun- = solidity{ slime / stew / secretion / mist / smoke / dust / vapor }
#. -passive-action-word- = exploded / vaporized / melted / sublimated / evaporated / transformed / calcified / vanished / faded / disappeared / shrivelled / bloated / liquefied / was lost / was misplaced / was bartered
#. -time-comma- = longtime{ -maybe-comma- / , / -maybe-comma- / -maybe-comma- / -maybe-comma- / -maybe-comma- / -maybe-comma- / , }
#. -maybe-comma- = [2] () / [1] ,
#. -time- = longtime{ one -day-weather- -day-part- / one -day-weather- -day-part- last -time-unit- / last -day-of-week- / last -time-unit- / -a-an- -time-unit- ago / on -holiday- / last -holiday- / -a-an- -time-unit- ago -holiday- / -two-to-six- -time-unit- -adjoining- s ago / -travel-time- }
#. -travel-time- = ([2] while / [1] whilst) (on safari to / exploring / on an expedition to / hunting in / on sabbatical in) -travel-place-
#. -travel-place- = Mozambique / Uganda / the Seychelles / the Vatican / Peoria / Borneo / Antarctica / Somerville / Northumberland / Saxony / Brugges / Gondwanaland
#. -holiday- = Christmas / Boxing Day / St. Swithin's Day
#. -day-of-week- = Monday / Tuesday / Wednesday / Thursday / Friday / Saturday
#. -day-part- = day / afternoon / morning / evening
#. -time-unit- = week / month / season
#. -day-weather- = [1] (rainy / foggy / blistering / blustery / gloomy / dank) / [2] ()
#. -two-to-six- = two / three / four / five / six / some
#. -person-description- = -name- ([2] -comma-description-phrase- / [1] ())
#. -comma-description-phrase- = , -a-an- ([1] -person-adjective- / [1] ()) -descriptor- ([1] -descriptor-modifier- / [2] ()) ,
#. -descriptor-modifier- = of -intensifier- (perspicacity / fortitude / passion / wit / perception / presence of mind)
#. -descriptor- = [1] -neutral-descriptor- / [1] (gender{ -male-descriptor- / -female-descriptor- })
#. -female-descriptor- = young miss / girl / maiden / flapper
#. -male-descriptor- = stalwart / gentleman / boy / youth
#. -neutral-descriptor- = toddler / aesthete / writer / artist
#. -intensifier- = great / some / considerable / not inconsiderable / distinct / impressive / unique / notable
#. -person-adjective- = precocious / unflappable / energetic / forceful / inimitable / daring / mild / intense / jaded
#. -he-she- = gender{ he / she }
#. -name- = gender{ -male-name- / -female-name- }
#. -male-name- = Bernard / Joseph / Emmett / Ogden / Eugene / Xerxes / Joshua / Lemuel / Etienne
#. -female-name- = Emmalissa / Chloe / Tiffani / Eunice / Zoe / Jennifer / Imelda / Yvette / Melantha

## wake = open('mutagen/wake.js').read()
## translate(wake)
#. -wake-root- = -drinking-sentence- / -river-march-sentence-
#. -drinking-sentence- = -drinking-sub-sentence- ([1] () / [1] -action-gloss-)
#. -drinking-sub-sentence- = -people- -drink-action- / -people- -side-action- and -drink-action- / -people- -side-action- , -side-action- , and -drink-action-
#. -river-march-sentence- = -people- -march-verb- (along / up / down) -river-road- ([1] () / [1] -action-gloss-) / (along / up / down) -river-road- ([1] () / [1] -locale-gloss-) -march-verb- -people- ([1] () / [1] -action-gloss-)
#. -action-gloss- = , ((spreading / sowing / leaving) (chaos / disaster / wrack and disaster) in their wake / (turning / transfiguring / transforming) (the world / all around / everything) into -a-an- (circus / carnival) (() / () / of their own making / of their own design) / (undertaking / preparing / investing) their best (effort / determination / and their most impassioned / () / ()) / as if (the world were their -bivalve- / nothing could be finer / the world had been made for them / they had been created for this day) / (at almost / almost at / at nearly / nearly at / approaching / having achieved) the end of -a-journey- / making the best of -a-journey- / (refusing / denying / disavowing / repudiating) (any / all / the slightest) thought of consequence (() / or causality) / making -a-an- (() / () / holy / unholy / disreputable) (spectacle / display / curiosity) of themselves (() / and their cause / and everyone around them)) ,
#. -side-action- = -side-verb- / -side-verb- / -side-verb- / -side-verb- with (great / some / () / () / ()) (vigor / vim / energy / gusto / enthusiasm) / -tone-adv- -side-verb- / -side-verb- -tone-adv- / -side-verb- (most / quite) -tone-adv-
#. -side-verb- = { stood / congregated / argued / fought / expostulated / shoved / prayed / sang / danced / lectured / remonstrated / pounded the table / banged their mugs / insulted each other / told stories / remembered old times / demanded satisfaction }
#. -drink-action- = -drank- -whiskey- / (drank / imbibed) prodigiously / -drank- prodigious quantities of -whiskey-
#. -drank- = drank / consumed / imbibed / partook of
#. -whiskey- = their whiskey / whiskey / poteen / moonshine / spirits / alcoholic spirits / strong drink / liquor / strong liquor
#. -a-journey- = a journey / a difficult journey / a long and difficult journey / their travels / their travails / (a / a sort of) journey (I need not describe / that need hardly be described) / (a / the sort of) journey sure to be immortalized (() / () / in legend / in history / in song)
#. -bivalve- = oyster / oyster / oyster / clam / cockle (or mussel, or other bivalve)
#. -locale-gloss- = , (a place hitherto (not troubled by such / untroubled by such / not so troubled) / (far / away / far away) from the (travails / clamour / bustle) of home / below the (() / green / high / high green) (hills / foothills / bluffs) / -a-an- (peaceable / quiet / peaceable and quiet) country (() / betimes / in better times) / above the (grimy / slimy / decaying / weed-wracked / chilly north) harbor / (round the bend / past stone / through heather) and (straightaway / off away / up the field / over bridge)) ,
#. -river-road- = the river / the road / the river road / the river -river-name- / the -river-name- river / the -place-name- road / the road (from / to) -place-name- / into -place-name-
#. -river-name- = Arney / Bann / Boyne / Boyle / Blackwater / Clare / Dargyle / Derry / Erne / Fergus / Liffey / Mourne / Nore / Shannon / Tweed / Tyne / Wye / Avon / Tay
#. -place-name- = Derby / Cork / Mayo / Dublin / Carlow / Kerry / Clare / Wexford / Leith / Lyke / Fife / Falkirk
#. -march-verb- = marched / went marching / came marching / paraded / walked / came walking / proceeded
#. -people- = -people-phrase- ([1] () / [1] , -tone-adj- ,) ([1] () / [1] , -tone-adj- and -tone-adj- ,) ([3] () / [1] -people-dash-gloss-)
#. -people-dash-gloss- = -- ((masters / lords and masters / lords) of all they (surveyed / might survey) / (monstrous / exorbitant) in (their / every / their every / face and) aspect / -willing- to take on all (comers / mankind / who came before them / who stood before them) / (affronting / an affront to / offending / an offense to / a challenge to) God and all mankind / -willing- to (storm / assault) the (gates / armies / will / decree / will and decree) of (Heaven / paradise) / motivated by the (best and worst / best / worst) in the hearts of (mankind / humanity / the human race) / -unstoppable- and (entirely / wholly / () / ()) -unstoppable- / as (unlikely / absurd / preposterous / laughable) -a-an- -group-word- of (lunatics / reprobates / Bedlamites) as (you're ever like to see / you'd ever want to see / you could find / one might find)) --
#. -unstoppable- = { unstoppable / uncontainable / unquenchable / irrepressible / insuppressible }
#. -willing- = willing and able / ready / ready and able / prepared
#. -tone-adv- = { energetically / enthustiastically / vigorously / noisily / uproariously / stridently / vociferously / riotously / rancorously / clamorously / obstreperously / boisterously / defiantly }
#. -tone-adj- = { rancorous / clamorous / obstreperous / boisterous / defiant / baleful / churlish / perfidious / vindictive / railing / flailing / wailing / shouting / screaming / chanting / muttering / bellowing / chattering / uproarious / strident / vociferous / riotous / flamboyant / booming / howling at the moon / raising their voices / shaking their fists }
#. -people-phrase- = -group-desc- ([1] () / [1] (furious / weary / angry / determined / steadfast / steady / stolid / comical / overbearing / fearsome / gnarled)) ([1] () / [1] (old / old / bent / tall / upright / powerful)) -base-people-
#. -group-desc- = [2] the / [2] ((the / -a-an-) -group-word- of) / [1] ((the / ()) (six / eight / ten / dozen))
#. -group-word- = { crowd / group / cluster / party / mob / flurry }
#. -base-people- = men / women / ladies / men / women / farmers / factory-workers / soldiers / mourners
