:mod:`dirtyjson` --- JSON decoder
=================================

.. module:: dirtyjson
   :synopsis: Decode JSON data from dirty files.
.. moduleauthor:: Scott Maxwell <scott@codecobblers.com>

JSON (JavaScript Object Notation) <http://json.org> is a subset of JavaScript
syntax (ECMA-262 3rd edition) used as a lightweight data interchange format.

:mod:`dirtyjson` is a JSON decoder meant for extracting JSON-type data from .js
files. The returned data structure includes information about line and column
numbers, so you can output more useful error messages. The input can also
include single quotes, line comments, inline comments, dangling commas,
unquoted single-word keys, and hexadecimal and octal numbers.

The goal of :mod:`dirtyjson` is to read JSON objects out of files that are
littered with elements that do not fit the official JSON standard. By providing
line and column number contexts, a dirty JSON file can be used as source input
for a complex data parser or compiler.

:mod:`dirtyjson` exposes an API familiar to users of the standard library
:mod:`marshal` and :mod:`pickle` modules. However, :mod:`dirtyjson` provides
only the `load(s)` capability. To write JSON, use either the standard
:mod:`json` library or :mod:`simplejson`.

.. note::

   The code for :mod:`dirtyjson` is a fairly drastically rewritten version
   of the loader in :mod:`simplejson` so thanks go to Bob Ippolito of the
   :mod:`simplejson` project for providing such a nice starting point.

Development of dirtyjson happens on Github:
http://github.com/codecobblers/dirtyjson

Decoding JSON::

    >>> import dirtyjson
    >>> obj = [u'foo', {u'bar': [u'baz', None, 1.0, 2]}]
    >>> dirtyjson.loads('["foo", /* not fu*/ {bar: ['baz', null, 1.0, 2,]}] and then ignore this junk') == obj
    True
    >>> dirtyjson.loads('"\\"foo\\bar"') == u'"foo\x08ar'
    True
    >>> from simplejson.compat import StringIO
    >>> io = StringIO('["streaming API"]')
    >>> dirtyjson.load(io)[0] == 'streaming API'
    True

Using Decimal instead of float::

    >>> import dirtyjson
    >>> from decimal import Decimal
    >>> dirtyjson.loads('1.1', parse_float=Decimal) == Decimal('1.1')
    True


Basic Usage
-----------

.. function:: load(fp[, encoding[, parse_float[, parse_int[, parse_constant[, search_for_first_object]]]]])

   Performs the following translations in decoding by default:

   +---------------+-------------------------+
   | JSON          | Python                  |
   +===============+=========================+
   | object        | :class:`AttributedDict` |
   +---------------+-------------------------+
   | array         | :class:`AttributedList` |
   +---------------+-------------------------+
   | string        | unicode                 |
   +---------------+-------------------------+
   | number (int)  | int, long               |
   +---------------+-------------------------+
   | number (real) | float                   |
   +---------------+-------------------------+
   | true          | True                    |
   +---------------+-------------------------+
   | false         | False                   |
   +---------------+-------------------------+
   | null          | None                    |
   +---------------+-------------------------+

   It also understands ``NaN``, ``Infinity``, and ``-Infinity`` as their
   corresponding ``float`` values, which is outside the JSON spec.

   Deserialize *fp* (a ``.read()``-supporting file-like object containing a JSON
   document) to a Python object. :exc:`dirtyjson.Error` will be
   raised if the given document is not valid.

   If the contents of *fp* are encoded with an ASCII based encoding other than
   UTF-8 (e.g. latin-1), then an appropriate *encoding* name must be specified.
   Encodings that are not ASCII based (such as UCS-2) are not allowed, and
   should be wrapped with ``codecs.getreader(fp)(encoding)``, or simply decoded
   to a :class:`unicode` object and passed to :func:`loads`. The default
   setting of ``'utf-8'`` is fastest and should be using whenever possible.

   If *fp.read()* returns :class:`str` then decoded JSON strings that contain
   only ASCII characters may be parsed as :class:`str` for performance and
   memory reasons. If your code expects only :class:`unicode` the appropriate
   solution is to wrap fp with a reader as demonstrated above.

   *parse_float*, if specified, will be called with the string of every JSON
   float to be decoded. By default, this is equivalent to ``float(num_str)``.
   This can be used to use another datatype or parser for JSON floats
   (e.g. :class:`decimal.Decimal`).

   *parse_int*, if specified, will be called with the int of the string of every
   JSON int to be decoded. By default, this is equivalent to ``int(num_str)``.
   This can be used to use another datatype or parser for JSON integers
   (e.g. :class:`float`).

   .. note::

      Unlike the standard :mod:`json` module, :mod:`dirtyjson` always does
      ``int(num_str, 0)`` before passing through to the converter passed is as
      the *parse_int* parameter. This is to enable automatic handling of hex
      and octal numbers.

   *parse_constant*, if specified, will be called with one of the following
   strings: ``true``, ``false``, ``null``, ``'-Infinity'``, ``'Infinity'``,
   ``'NaN'``. This can be used to raise an exception if invalid JSON numbers are
   encountered or to provide alternate values for any of these constants.

   *search_for_first_object*, if ``True``, will cause the parser to search for
   the first occurrence of either ``{`` or ``[``. This is very useful for
   reading an object from a JavaScript file.

.. function:: loads(s[, encoding[, parse_float[, parse_int[, parse_constant[, search_for_first_object[, start_index]]]]])

   Deserialize *s* (a :class:`str` or :class:`unicode` instance containing a JSON
   document) to a Python object. :exc:`dirtyjson.Error` will be
   raised if the given JSON document is not valid.

   If *s* is a :class:`str` instance and is encoded with an ASCII based encoding
   other than UTF-8 (e.g. latin-1), then an appropriate *encoding* name must be
   specified. Encodings that are not ASCII based (such as UCS-2) are not
   allowed and should be decoded to :class:`unicode` first.

   If *s* is a :class:`str` then decoded JSON strings that contain
   only ASCII characters may be parsed as :class:`str` for performance and
   memory reasons. If your code expects only :class:`unicode` the appropriate
   solution is decode *s* to :class:`unicode` prior to calling loads.

   *start_index*, if non-zero, will cause the parser to start processing from
   the specified offset, while maintaining the correct line and column numbers.
   This is very useful for reading an object from the middle of a JavaScript
   file.

   The other arguments have the same meaning as in :func:`load`.

Exceptions
----------

.. exception:: dirtyjson.Error(msg, doc, pos)

    Subclass of :exc:`ValueError` with the following additional attributes:

    .. attribute:: msg

        The unformatted error message

    .. attribute:: doc

        The JSON document being parsed

    .. attribute:: pos

        The start index of doc where parsing failed

    .. attribute:: lineno

        The line corresponding to pos

    .. attribute:: colno

        The column corresponding to pos

AttributedDict and AttributedList
---------------------------------

The :mod:`dirtyjson` module uses :class:`AttributedDict` and
:class:`AttributedList` instead of ``dict`` and ``list``. Each is actually a
subclass of its base type (``dict`` or ``list``) and can be used as if they were
the standard class, but these have been enhanced to store attributes with each
element. We use those attributes to store line and column numbers. You can use
that information to refer users back to the exact location in the original
source file.

.. class:: AttributedDict()

   A subclass of ``dict`` that behaves exactly like a ``dict`` except that it
   maintains order like an ``OrderedDict`` and allows storing attributes for
   each key/value pair.

   .. method:: add_with_attributes(self, key, value, attributes)

      Set the *key* in the underlying ``dict`` to the *value* and also store
      whatever is passed in as *attributes* for later retrieval. In our case,
      we store an attrbute ``dict`` that looks like::

         {'key': (key_line_no, key_column_no), 'value': (value_line_no, value_column_no)}

   .. method:: attributes(self, key)

      Return the attributes associated with the specified *key* or ``None`` if
      no attributes exist for the key.

.. class:: AttributedList()

   A subclass of ``list`` that behaves exactly like a ``list`` except that it
   allows storing attributes for each value.

   .. method:: append(self, value, attributes=None):

      Appends *value* to the list and *attributes* to the associated location.
      In our case, we store an attribute tuple that looks like::

         (value_line_no, value_column_no)

   .. method:: attributes(self, index)

      Returns the attributes for the value at the given *index*.

   .. note::

      This class is *NOT* robust. If you insert or delete items, the attributes
      will get out of sync. Making this a non-naive class would be a nice
      enhancement.
