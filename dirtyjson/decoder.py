"""Implementation of JSONDecoder
"""
from __future__ import absolute_import
import re
import sys
import struct
from .compat import fromhex, u, text_type, binary_type, PY2, unichr
from dirtyjson.attributed_dict import AttributedDict
from .error import JSONDecodeError


__all__ = ['JSONDecoder']

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL


def _floatconstants():
    _BYTES = fromhex('7FF80000000000007FF0000000000000')
    # The struct module in Python 2.4 would get frexp() out of range here
    # when an endian is specified in the format string. Fixed in Python 2.5+
    if sys.byteorder != 'big':
        _BYTES = _BYTES[:8][::-1] + _BYTES[8:][::-1]
    nan, inf = struct.unpack('dd', _BYTES)
    return nan, inf, -inf

NaN, PosInf, NegInf = _floatconstants()

_CONSTANTS = {
    '-Infinity': NegInf,
    'Infinity': PosInf,
    'NaN': NaN,
}

NUMBER_RE = re.compile(
    r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?',
    (re.VERBOSE | re.MULTILINE | re.DOTALL))
STRINGCHUNK = re.compile(r'(.*?)(["\\\x00-\x1f])', FLAGS)
BACKSLASH = {
    '"': u('"'), '\\': u('\u005c'), '/': u('/'),
    'b': u('\b'), 'f': u('\f'), 'n': u('\n'), 'r': u('\r'), 't': u('\t'),
}

DEFAULT_ENCODING = "utf-8"
WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)
WHITESPACE_STR = ' \t\n\r'


class JSONDecoder(object):
    """Simple JSON <http://json.org> decoder

    Performs the following translations in decoding by default:

    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | object        | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    | string        | unicode           |
    +---------------+-------------------+
    | number (int)  | int, long         |
    +---------------+-------------------+
    | number (real) | float             |
    +---------------+-------------------+
    | true          | True              |
    +---------------+-------------------+
    | false         | False             |
    +---------------+-------------------+
    | null          | None              |
    +---------------+-------------------+

    It also understands ``NaN``, ``Infinity``, and ``-Infinity`` as
    their corresponding ``float`` values, which is outside the JSON spec.

    """

    def __init__(self, encoding=None, parse_float=None, parse_int=None,
                 parse_constant=None):
        """
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

        """
        self.encoding = encoding or DEFAULT_ENCODING
        self.parse_float = parse_float or float
        self.parse_int = parse_int or int
        self.parse_constant = parse_constant or _CONSTANTS.__getitem__
        self.memo = {}

    def _scan_once(self, string, idx):
        error_message = 'Expecting value'
        try:
            nextchar = string[idx]
        except IndexError:
            raise JSONDecodeError(error_message, string, idx)

        if nextchar == '"':
            return self.scanstring(string, idx + 1)
        elif nextchar == '{':
            return self.parse_object(string, idx + 1)
        elif nextchar == '[':
            return self.parse_array(string, idx + 1)
        elif nextchar == 'n' and string[idx:idx + 4] == 'null':
            return None, idx + 4
        elif nextchar == 't' and string[idx:idx + 4] == 'true':
            return True, idx + 4
        elif nextchar == 'f' and string[idx:idx + 5] == 'false':
            return False, idx + 5

        m = NUMBER_RE.match(string, idx)
        if m is not None:
            integer, frac, exp = m.groups()
            if frac or exp:
                res = self.parse_float(integer + (frac or '') + (exp or ''))
            else:
                res = self.parse_int(integer)
            return res, m.end()
        elif nextchar == 'N' and string[idx:idx + 3] == 'NaN':
            return self.parse_constant('NaN'), idx + 3
        elif nextchar == 'I' and string[idx:idx + 8] == 'Infinity':
            return self.parse_constant('Infinity'), idx + 8
        elif nextchar == '-' and string[idx:idx + 9] == '-Infinity':
            return self.parse_constant('-Infinity'), idx + 9
        else:
            raise JSONDecodeError(error_message, string, idx)

    def scanstring(self, string, end,
                   _b=BACKSLASH, _m=STRINGCHUNK.match, _join=u('').join,
                   _py2=PY2, _maxunicode=sys.maxunicode):
        """Scan the string for a JSON string. End is the index of the
        character in string after the quote that started the JSON string.
        Unescapes all valid JSON string escape sequences and raises ValueError
        on attempt to decode an invalid string. If strict is False then literal
        control characters are allowed in the string.

        Returns a tuple of the decoded string and the index of the character in
        string after the end quote."""
        chunks = []
        _append = chunks.append
        begin = end - 1
        while 1:
            chunk = _m(string, end)
            if chunk is None:
                raise JSONDecodeError(
                    "Unterminated string starting at", string, begin)
            end = chunk.end()
            content, terminator = chunk.groups()
            # Content is contains zero or more unescaped string characters
            if content:
                if _py2 and not isinstance(content, text_type):
                    content = text_type(content, self.encoding)
                _append(content)
            # Terminator is the end of string, a literal control character,
            # or a backslash denoting that an escape sequence follows
            if terminator == '"':
                break
            elif terminator != '\\':
                _append(terminator)
                continue
            try:
                esc = string[end]
            except IndexError:
                raise JSONDecodeError(
                    "Unterminated string starting at", string, begin)
            # If not a unicode escape sequence, must be in the lookup table
            if esc != 'u':
                try:
                    char = _b[esc]
                except KeyError:
                    msg = "Invalid \\X escape sequence %r"
                    raise JSONDecodeError(msg, string, end)
                end += 1
            else:
                # Unicode escape sequence
                msg = "Invalid \\uXXXX escape sequence"
                esc = string[end + 1:end + 5]
                esc_x = esc[1:2]
                if len(esc) != 4 or esc_x == 'x' or esc_x == 'X':
                    raise JSONDecodeError(msg, string, end - 1)
                try:
                    uni = int(esc, 16)
                except ValueError:
                    raise JSONDecodeError(msg, string, end - 1)
                end += 5
                # Check for surrogate pair on UCS-4 systems
                # Note that this will join high/low surrogate pairs
                # but will also pass unpaired surrogates through
                if _maxunicode > 65535 and uni & 0xfc00 == 0xd800 and string[end:end + 2] == '\\u':
                    esc2 = string[end + 2:end + 6]
                    esc_x = esc2[1:2]
                    if len(esc2) == 4 and not (esc_x == 'x' or esc_x == 'X'):
                        try:
                            uni2 = int(esc2, 16)
                        except ValueError:
                            raise JSONDecodeError(msg, string, end)
                        if uni2 & 0xfc00 == 0xdc00:
                            uni = 0x10000 + (((uni - 0xd800) << 10) |
                                             (uni2 - 0xdc00))
                            end += 6
                char = unichr(uni)
            # Append the unescaped character
            _append(char)
        return _join(chunks), end

    def parse_object(self, string, end,
                     _w=WHITESPACE.match, _ws=WHITESPACE_STR):
        # Backwards compatibility
        memo_get = self.memo.setdefault
        pairs = []
        # Use a slice to prevent IndexError from being raised, the following
        # check will raise a more specific ValueError if the string is empty
        nextchar = string[end:end + 1]
        # Normally we expect nextchar == '"'
        if nextchar != '"':
            if nextchar in _ws:
                end = _w(string, end).end()
                nextchar = string[end:end + 1]
            # Trivial empty object
            if nextchar == '}':
                return AttributedDict(pairs), end + 1
            elif nextchar != '"':
                raise JSONDecodeError(
                    "Expecting property name enclosed in double quotes",
                    string, end)
        end += 1
        while True:
            key, end = self.scanstring(string, end)
            key = memo_get(key, key)

            # To skip some function call overhead we optimize the fast paths where
            # the JSON key separator is ": " or just ":".
            if string[end:end + 1] != ':':
                end = _w(string, end).end()
                if string[end:end + 1] != ':':
                    raise JSONDecodeError("Expecting ':' delimiter", string, end)

            end += 1

            try:
                if string[end] in _ws:
                    end += 1
                    if string[end] in _ws:
                        end = _w(string, end + 1).end()
            except IndexError:
                pass

            value, end = self._scan_once(string, end)
            pairs.append((key, value))

            try:
                nextchar = string[end]
                if nextchar in _ws:
                    end = _w(string, end + 1).end()
                    nextchar = string[end]
            except IndexError:
                nextchar = ''
            end += 1

            if nextchar == '}':
                break
            elif nextchar != ',':
                raise JSONDecodeError("Expecting ',' delimiter or '}'", string, end - 1)

            try:
                nextchar = string[end]
                if nextchar in _ws:
                    end += 1
                    nextchar = string[end]
                    if nextchar in _ws:
                        end = _w(string, end + 1).end()
                        nextchar = string[end]
            except IndexError:
                nextchar = ''

            end += 1
            if nextchar != '"':
                raise JSONDecodeError(
                    "Expecting property name enclosed in double quotes",
                    string, end - 1)

        return AttributedDict(pairs), end

    def parse_array(self, string, end, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
        values = []
        nextchar = string[end:end + 1]
        if nextchar in _ws:
            end = _w(string, end + 1).end()
            nextchar = string[end:end + 1]
        # Look-ahead for trivial empty array
        if nextchar == ']':
            return values, end + 1
        elif nextchar == '':
            raise JSONDecodeError("Expecting value or ']'", string, end)
        _append = values.append
        while True:
            value, end = self._scan_once(string, end)
            _append(value)
            nextchar = string[end:end + 1]
            if nextchar in _ws:
                end = _w(string, end + 1).end()
                nextchar = string[end:end + 1]
            end += 1
            if nextchar == ']':
                break
            elif nextchar != ',':
                raise JSONDecodeError("Expecting ',' delimiter or ']'", string, end - 1)

            try:
                if string[end] in _ws:
                    end += 1
                    if string[end] in _ws:
                        end = _w(string, end + 1).end()
            except IndexError:
                pass

        return values, end

    def scan_once(self, string, idx):
        try:
            return self._scan_once(string, idx)
        finally:
            self.memo.clear()

    def decode(self, s, _w=WHITESPACE.match):
        """Return the Python representation of ``s`` (a ``str`` or ``unicode``
        instance containing a JSON document)

        """
        if not PY2 and isinstance(s, binary_type):
            s = s.decode(self.encoding)
        obj, end = self.raw_decode(s)
        end = _w(s, end).end()
        if end != len(s):
            raise JSONDecodeError("Extra data", s, end, len(s))
        return obj

    def raw_decode(self, s, idx=0, _w=WHITESPACE.match):
        """Decode a JSON document from ``s`` (a ``str`` or ``unicode``
        beginning with a JSON document) and return a 2-tuple of the Python
        representation and the index in ``s`` where the document ended.
        Optionally, ``idx`` can be used to specify an offset in ``s`` where
        the JSON document begins.

        This can be used to decode a JSON document from a string that may
        have extraneous data at the end.

        """
        if not PY2 and not isinstance(s, text_type):
            raise TypeError("Input string must be text, not bytes")
        return self.scan_once(s, idx=_w(s, idx).end())
