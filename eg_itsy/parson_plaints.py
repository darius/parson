"""
Format parse errors with a vaguely-friendly display of the position.
TODO something like this ought to come with Parson itself
"""

def syntax_error(exc, filename):
    line_no, prefix, suffix = where(exc)
    prefix, suffix = sanitize(prefix), sanitize(suffix)
    return '\n'.join(["%s:%d:%d: Syntax error\n" % (filename, line_no, len(prefix)),
                      '  ' + prefix + suffix,
                      '  ' + ' '*len(prefix) + '^'])

def where(exc):
    before, after = exc.failure
    line_no = before.count('\n')
    prefix = (before+'\n').splitlines()[line_no]
    suffix = (after+'\n').splitlines()[0] # XXX what if right on newline?
    return line_no+1, prefix, suffix

def sanitize(s):
    "Make s predictably printable, sans control characters like tab."
    return ''.join(c if ' ' <= c < chr(127) else ' ' # XXX crude
                   for c in s)
