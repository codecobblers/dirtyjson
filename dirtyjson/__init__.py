r"""JSON (JavaScript Object Notation) <http://json.org> is a subset of
JavaScript syntax (ECMA-262 3rd edition) used as a lightweight data
interchange format.

:mod:`dirtyjson` exposes an API familiar to users of the standard library
:mod:`marshal` and :mod:`pickle` modules. It is the externally maintained
version of the :mod:`json` library contained in Python 2.6, but maintains
compatibility with Python 2.4 and Python 2.5 and (currently) has
significant performance advantages, even without using the optional C
extension for speedups.

Decoding JSON::

    >>> import dirtyjson
    >>> obj = [u'foo', {u'bar': [u'baz', None, 1.0, 2]}]
    >>> dirtyjson.loads('["foo", {"bar":["baz", null, 1.0, 2]}]') == obj
    True
    >>> dirtyjson.loads('"\\"foo\\bar"') == u'"foo\x08ar'
    True
    >>> from dirtyjson.compat import StringIO
    >>> io = StringIO('["streaming API"]')
    >>> dirtyjson.load(io)[0] == 'streaming API'
    True

Specializing JSON object decoding::

    >>> import dirtyjson
    >>> def as_complex(dct):
    ...     if '__complex__' in dct:
    ...         return complex(dct['real'], dct['imag'])
    ...     return dct
    ...
    >>> dirtyjson.loads('{"__complex__": true, "real": 1, "imag": 2}',
    ...     object_hook=as_complex)
    (1+2j)
    >>> from decimal import Decimal
    >>> dirtyjson.loads('1.1', parse_float=Decimal) == Decimal('1.1')
    True

"""
from __future__ import absolute_import
__version__ = '3.3.0'
__all__ = [
    'dump', 'dumps', 'load', 'loads',
    'JSONDecoder', 'JSONDecodeError', 'JSONEncoder',
    'OrderedDict',
]

__author__ = 'Bob Ippolito <bob@redivi.com>'

from decimal import Decimal

from .scanner import JSONDecodeError
from .decoder import JSONDecoder


def _import_ordereddict():
    import collections
    try:
        return collections.OrderedDict
    except AttributeError:
        from . import ordered_dict
        return ordered_dict.OrderedDict
OrderedDict = _import_ordereddict()


_default_decoder = JSONDecoder(encoding=None, object_hook=None,
                               object_pairs_hook=None)


def load(fp, encoding=None, cls=None, object_hook=None, parse_float=None,
         parse_int=None, parse_constant=None, object_pairs_hook=None,
         use_decimal=False, **kw):
    """Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a JSON document) to a Python object.

    *encoding* determines the encoding used to interpret any
    :class:`str` objects decoded by this instance (``'utf-8'`` by
    default).  It has no effect when decoding :class:`unicode` objects.

    Note that currently only encodings that are a superset of ASCII work,
    strings of other encodings should be passed in as :class:`unicode`.

    *object_hook*, if specified, will be called with the result of every
    JSON object decoded and its return value will be used in place of the
    given :class:`dict`.  This can be used to provide custom
    deserializations (e.g. to support JSON-RPC class hinting).

    *object_pairs_hook* is an optional function that will be called with
    the result of any object literal decode with an ordered list of pairs.
    The return value of *object_pairs_hook* will be used instead of the
    :class:`dict`.  This feature can be used to implement custom decoders
    that rely on the order that the key and value pairs are decoded (for
    example, :func:`collections.OrderedDict` will remember the order of
    insertion). If *object_hook* is also defined, the *object_pairs_hook*
    takes priority.

    *parse_float*, if specified, will be called with the string of every
    JSON float to be decoded.  By default, this is equivalent to
    ``float(num_str)``. This can be used to use another datatype or parser
    for JSON floats (e.g. :class:`decimal.Decimal`).

    *parse_int*, if specified, will be called with the string of every
    JSON int to be decoded.  By default, this is equivalent to
    ``int(num_str)``.  This can be used to use another datatype or parser
    for JSON integers (e.g. :class:`float`).

    *parse_constant*, if specified, will be called with one of the
    following strings: ``'-Infinity'``, ``'Infinity'``, ``'NaN'``.  This
    can be used to raise an exception if invalid JSON numbers are
    encountered.

    If *use_decimal* is true (default: ``False``) then it implies
    parse_float=decimal.Decimal for parity with ``dump``.

    To use a custom ``JSONDecoder`` subclass, specify it with the ``cls``
    kwarg. NOTE: You should use *object_hook* or *object_pairs_hook* instead
    of subclassing whenever possible.

    """
    return loads(fp.read(),
                 encoding=encoding, cls=cls, object_hook=object_hook,
                 parse_float=parse_float, parse_int=parse_int,
                 parse_constant=parse_constant,
                 object_pairs_hook=object_pairs_hook,
                 use_decimal=use_decimal, **kw)


def loads(s, encoding=None, cls=None, object_hook=None, parse_float=None,
          parse_int=None, parse_constant=None, object_pairs_hook=None,
          use_decimal=False, **kw):
    """Deserialize ``s`` (a ``str`` or ``unicode`` instance containing a JSON
    document) to a Python object.

    *encoding* determines the encoding used to interpret any
    :class:`str` objects decoded by this instance (``'utf-8'`` by
    default).  It has no effect when decoding :class:`unicode` objects.

    Note that currently only encodings that are a superset of ASCII work,
    strings of other encodings should be passed in as :class:`unicode`.

    *object_hook*, if specified, will be called with the result of every
    JSON object decoded and its return value will be used in place of the
    given :class:`dict`.  This can be used to provide custom
    deserializations (e.g. to support JSON-RPC class hinting).

    *object_pairs_hook* is an optional function that will be called with
    the result of any object literal decode with an ordered list of pairs.
    The return value of *object_pairs_hook* will be used instead of the
    :class:`dict`.  This feature can be used to implement custom decoders
    that rely on the order that the key and value pairs are decoded (for
    example, :func:`collections.OrderedDict` will remember the order of
    insertion). If *object_hook* is also defined, the *object_pairs_hook*
    takes priority.

    *parse_float*, if specified, will be called with the string of every
    JSON float to be decoded.  By default, this is equivalent to
    ``float(num_str)``. This can be used to use another datatype or parser
    for JSON floats (e.g. :class:`decimal.Decimal`).

    *parse_int*, if specified, will be called with the string of every
    JSON int to be decoded.  By default, this is equivalent to
    ``int(num_str)``.  This can be used to use another datatype or parser
    for JSON integers (e.g. :class:`float`).

    *parse_constant*, if specified, will be called with one of the
    following strings: ``'-Infinity'``, ``'Infinity'``, ``'NaN'``.  This
    can be used to raise an exception if invalid JSON numbers are
    encountered.

    If *use_decimal* is true (default: ``False``) then it implies
    parse_float=decimal.Decimal for parity with ``dump``.

    To use a custom ``JSONDecoder`` subclass, specify it with the ``cls``
    kwarg. NOTE: You should use *object_hook* or *object_pairs_hook* instead
    of subclassing whenever possible.

    """
    if (cls is None and encoding is None and object_hook is None and
            parse_int is None and parse_float is None and
            parse_constant is None and object_pairs_hook is None
            and not use_decimal and not kw):
        return _default_decoder.decode(s)
    if cls is None:
        cls = JSONDecoder
    if object_hook is not None:
        kw['object_hook'] = object_hook
    if object_pairs_hook is not None:
        kw['object_pairs_hook'] = object_pairs_hook
    if parse_float is not None:
        kw['parse_float'] = parse_float
    if parse_int is not None:
        kw['parse_int'] = parse_int
    if parse_constant is not None:
        kw['parse_constant'] = parse_constant
    if use_decimal:
        if parse_float is not None:
            raise TypeError("use_decimal=True implies parse_float=Decimal")
        kw['parse_float'] = Decimal
    return cls(encoding=encoding, **kw).decode(s)
