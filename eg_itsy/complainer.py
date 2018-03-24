"""
Format parse errors with a vaguely-friendly display of the position.
TODO Parson itself ought to help with something like this
TODO Position info needs to be a range, not a single coordinate.
     Or at least point to the '+' in 'a+a' instead of to the 'a'.
"""

from structs import Struct
import sys

status_ok, status_error = range(2)

class Complainer(object):

    def __init__(self, text, filename):
        self.text = text
        self.filename = filename
        self.status = status_ok

    def ok(self):
        return self.status == status_ok

    def syntax_error(self, exc):
        self.complain(exc.failure, "Syntax error")

    def semantic_error(self, plaint, pos):
        self.complain((self.text[:pos], self.text[pos:]), plaint)

    def complain(self, (before, after), plaint):
        self.status = status_error
        line_no = before.count('\n')
        prefix = (before+'\n').splitlines()[line_no]
        suffix = (after+'\n').splitlines()[0] # XXX what if right on newline?
        prefix, suffix = sanitize(prefix), sanitize(suffix)
        message = ["%s:%d:%d: %s" % (self.filename, line_no+1, len(prefix), plaint),
                   '  ' + prefix + suffix,
                   '  ' + ' '*len(prefix) + '^']
        sys.stderr.write('\n'.join(message) + '\n')

def sanitize(s):
    "Make s predictably printable, sans control characters like tab."
    return ''.join(c if ' ' <= c < chr(127) else ' ' # XXX crude
                   for c in s)
