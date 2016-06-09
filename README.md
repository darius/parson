parson
======

Yet another PEG parser combinator library in Python. Selling points:

  * The optional concrete syntax for grammars incorporates semantic
    actions in a concise host-language-independent way. A Parson
    grammar won't tie you to Python.

  * Whole grammars can be analyzed and compiled, even if built at
    runtime using combinators. (Contrast with a monadic library, where
    this is uncomputable.)

  * Semantic actions take and return values in a kind of point-free
    style. 

  * You can use the concrete syntax with about as little ceremony as
    `re.match`.

  * You can parse non-string sequences.

Anti-selling points:

  * This library's in fluid design still, undocumented, utterly
    untuned, etc. I'd like you to use it if you think you might give
    feedback on the design; otherwise, no promises.

  * Semantic actions work in a nontraditional way that may remind you
    of Forth and which I haven't yet tried to make play well in typed
    languages like Haskell. It's concise and just right for parsing,
    but maybe in the end it'll turn out too cute and make me rip it
    out if I want this to be used.

  * I don't intend to make grammars work in other host languages
    before the design settles. (I have done this a bit for the
    [Peglet](https://github.com/darius/peglet) library, a more basic
    and settled expression of the same approach to actions: it has
    Python and JavaScript ports.)

I guess the most similar library out there is LPEG, and that's way way
more polished.


Examples
========

For now, see all the eg_whatever.py files here. eg_calc.py,
eg_misc.py, eg_wc.py, and eg_regex.py have the smallest ones.
eg_trees.py shows parsing of tree structures, OMeta-style. Other
examples include programming languages and other somewhat-bigger
stuff.

Basic things still to explain:
  * grammar syntax
  * combinators
  * recursion with combinators
  * actions

Examples of where I've used it for more than examples:
  * [IDEAL](https://github.com/darius/unreal/blob/master/parser.py), a drawing language
  * [Linogram](https://github.com/darius/goobergram/blob/master/parser.py), also a drawing language
  * [Pythological](https://github.com/darius/pythological/blob/master/parser.py), a MiniKanren with a vaguely Prologish frontend
  * [tinyhiss](https://github.com/darius/tinyhiss/blob/master/parser.py) -- Smalltalkish
  * [Squee](https://github.com/darius/squee/blob/master/parse_sans_offsides.py), an experimental language not much like any others
