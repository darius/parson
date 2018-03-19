## Itsy is not C but can translate to it directly.

An example language inspired by the design goals of Per Vognsen's
[Ion](https://github.com/pervognsen/bitwise/blob/master/notes/ion_motivation.md)
language, but the syntax was slapped together mostly before seeing his
work. (The operator precedences are taken from Ion, though.) Also, I'm
pretty unconcerned about familiarity to C people.

Not finished, and I dunno if it ever will be.

The syntax for pointers and arrays (their declaration and use) has
appeared earlier in the SPECS alternative syntax for C++ (Ben Werther
& Damian Conway) and in Odin (...). I didn't get it from them but by
following the implications of a remark in Ritchie's "The Development
of the C Language": "Sethi observed that many of the nested
declarations and expressions would become simpler if the indirection
operator had been taken as a postfix operator instead of prefix". For
this he references R. Sethi, "Uniform Syntax for Type Expressions and
Declarators." Softw., Pract. Exper. 11 (6): 623-628
(1981). Unfortunately I can't find that paper online.
