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
following the implications of a remark long ago whose source I've
forgotten, saying that C declaration syntax would've worked readably
if only the prefix '*' operator had been postfix.
