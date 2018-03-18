"""
Define a named-tuple-like type, but simpler.
Also Visitor to dispatch on datatypes defined this way.
"""

# TODO figure out how to use __slots__

def Struct(field_names, name=None, supertype=(object,)):
    if isinstance(field_names, (str, unicode)):
        field_names = tuple(field_names.split())

    if name is None:
        name = 'Struct<%s>' % ','.join(field_names)
        def get_name(self): return self.__class__.__name__
    else:
        def get_name(self): return name

    def __init__(self, *args):
        if len(field_names) != len(args):
	    raise TypeError("%s takes %d arguments (%d given)"
                            % (get_name(self), len(field_names), len(args)))
        self.__dict__.update(zip(field_names, args))

    def __repr__(self):
        return '%s(%s)' % (get_name(self), ', '.join(repr(getattr(self, f))
                                                     for f in field_names))

    # (for use with pprint)
    def my_as_sexpr(self):         # XXX better name?
        return (get_name(self),) + tuple(as_sexpr(getattr(self, f))
                                         for f in field_names)
    my_as_sexpr.__name__ = 'as_sexpr'

    return type(name,
                supertype,
                dict(__init__=__init__,
                     __repr__=__repr__,
                     as_sexpr=my_as_sexpr))

def as_sexpr(obj):
    if hasattr(obj, 'as_sexpr'):
        return getattr(obj, 'as_sexpr')()
    elif isinstance(obj, list):
        return map(as_sexpr, obj)
    elif isinstance(obj, tuple):
        return tuple(map(as_sexpr, obj))
    else:
        return obj


# Is there a nicer way to do this?

class Visitor(object):
    def __call__(self, subject, *args):
        tag = subject.__class__.__name__
        method = getattr(self, tag, None)
        if method is None:
            method = getattr(self, 'default')
        return method(subject, *args)
