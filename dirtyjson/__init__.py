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
__version__ = '1.0.0'
__all__ = [
    'dump', 'dumps', 'load', 'loads',
    'JSONDecoder', 'JSONDecodeError', 'JSONEncoder',
    'AttributedDict',
]

__author__ = 'Scott Maxwell <scott@codecobblers.com>'

from decimal import Decimal

from .error import JSONDecodeError
from .decoder import JSONDecoder
from .attributed_dict import AttributedDict


def load(fp, encoding=None, parse_float=None, parse_int=None,
         parse_constant=None, use_decimal=False):
    """Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a JSON document) to a Python object.

    *encoding* determines the encoding used to interpret any
    :class:`str` objects decoded by this instance (``'utf-8'`` by
    default).  It has no effect when decoding :class:`unicode` objects.

    Note that currently only encodings that are a superset of ASCII work,
    strings of other encodings should be passed in as :class:`unicode`.

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
    """
    return loads(fp.read(),
                 encoding=encoding, parse_float=parse_float,
                 parse_int=parse_int, parse_constant=parse_constant,
                 use_decimal=use_decimal)


def loads(s, encoding=None, parse_float=None, parse_int=None,
          parse_constant=None, use_decimal=False):
    """Deserialize ``s`` (a ``str`` or ``unicode`` instance containing a JSON
    document) to a Python object.

    *encoding* determines the encoding used to interpret any
    :class:`str` objects decoded by this instance (``'utf-8'`` by
    default).  It has no effect when decoding :class:`unicode` objects.

    Note that currently only encodings that are a superset of ASCII work,
    strings of other encodings should be passed in as :class:`unicode`.

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
    """
    if use_decimal:
        if parse_float is not None:
            raise TypeError("use_decimal=True implies parse_float=Decimal")
        parse_float = Decimal
    return JSONDecoder(encoding=encoding, parse_float=parse_float, parse_int=parse_int, parse_constant=parse_constant).decode(s)
