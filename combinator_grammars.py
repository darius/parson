"""
A convenience for defining recursive grammars in the combinator DSL.
The delay() combinator works for this, but code using it is maybe uglier.
"""

import parson as P

class Grammar(object):   # XXX call it something else? name clash
    def __init__(self):
        object.__setattr__(self, '_rules', {})
        object.__setattr__(self, '_stubs', {})

    def __getattr__(self, name):
        try: return self._rules[name]
        except KeyError: pass
        try: return self._stubs[name]
        except KeyError: pass
        self._stubs[name] = result = P.delay(lambda: self._rules[name], '<%s>', name)
        return result

    def __setattr__(self, name, value):
        self._rules[name] = value

# Example:
## g = Grammar()
## g.a = 'A' + g.b
## g.b = 'B'
## g.a('AB')
#. ()

# TODO try fancier examples
# TODO investigate implementing via descriptors instead
# TODO nicer error when misused
