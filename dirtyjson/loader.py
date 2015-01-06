"""Implementation of JSONDecoder
"""
from __future__ import absolute_import
import re
import sys
import struct
from .compat import fromhex, u, text_type, binary_type, PY2, unichr
from dirtyjson.attributed_dict import AttributedDict
from .error import JSONDecodeError


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

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL
NUMBER_RE = re.compile(r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?', FLAGS)
STRINGCHUNK = re.compile(r'(.*?)(["\\\x00-\x1f])', FLAGS)
WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)
WHITESPACE_STR = ' \t\n\r'

BACKSLASH = {
    '"': u('"'), '\\': u('\u005c'), '/': u('/'),
    'b': u('\b'), 'f': u('\f'), 'n': u('\n'), 'r': u('\r'), 't': u('\t'),
}
DEFAULT_ENCODING = "utf-8"


class DirtyJSONLoader(object):
    """JSON decoder that can handle muck in the file

    Performs the following translations in decoding by default:

    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | object        | AttributedDict    |
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

    def __init__(self, content, encoding=None, parse_float=None, parse_int=None,
                 parse_constant=None):
        self.encoding = encoding or DEFAULT_ENCODING
        self.parse_float = parse_float or float
        self.parse_int = parse_int or int
        self.parse_constant = parse_constant or _CONSTANTS.__getitem__
        self.memo = {}
        self.content = content
        self.idx = 0

    def scan(self, string):
        error_message = 'Expecting value'
        try:
            nextchar = string[self.idx]
        except IndexError:
            raise JSONDecodeError(error_message, string, self.idx)

        if nextchar == '"':
            self.idx += 1
            return self.parse_string(string)
        elif nextchar == '{':
            self.idx += 1
            return self.parse_object(string)
        elif nextchar == '[':
            self.idx += 1
            return self.parse_array(string)
        elif nextchar == 'n' and string[self.idx:self.idx + 4] == 'null':
            self.idx += 4
            return None
        elif nextchar == 't' and string[self.idx:self.idx + 4] == 'true':
            self.idx += 4
            return True
        elif nextchar == 'f' and string[self.idx:self.idx + 5] == 'false':
            self.idx += 5
            return False

        m = NUMBER_RE.match(string, self.idx)
        if m is not None:
            integer, frac, exp = m.groups()
            if frac or exp:
                res = self.parse_float(integer + (frac or '') + (exp or ''))
            else:
                res = self.parse_int(integer)
            self.idx = m.end()
            return res
        elif nextchar == 'N' and string[self.idx:self.idx + 3] == 'NaN':
            self.idx += 3
            return self.parse_constant('NaN')
        elif nextchar == 'I' and string[self.idx:self.idx + 8] == 'Infinity':
            self.idx += 8
            return self.parse_constant('Infinity')
        elif nextchar == '-' and string[self.idx:self.idx + 9] == '-Infinity':
            self.idx += 9
            return self.parse_constant('-Infinity')
        else:
            raise JSONDecodeError(error_message, string, self.idx)

    def parse_string(self, string,
                     _b=BACKSLASH, _m=STRINGCHUNK.match, _join=u('').join,
                     _py2=PY2, _maxunicode=sys.maxunicode):
        """Scan the string for a JSON string. End is the index of the
        character in string after the quote that started the JSON string.
        Unescapes all valid JSON string escape sequences and raises ValueError
        on attempt to decode an invalid string.

        Returns a tuple of the decoded string and the index of the character in
        string after the end quote."""
        chunks = []
        _append = chunks.append
        begin = self.idx - 1
        while 1:
            chunk = _m(string, self.idx)
            if chunk is None:
                raise JSONDecodeError(
                    "Unterminated string starting at", string, begin)
            self.idx = chunk.end()
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
                esc = string[self.idx]
            except IndexError:
                raise JSONDecodeError(
                    "Unterminated string starting at", string, begin)
            # If not a unicode escape sequence, must be in the lookup table
            if esc != 'u':
                try:
                    char = _b[esc]
                except KeyError:
                    msg = "Invalid \\X escape sequence %r"
                    raise JSONDecodeError(msg, string, self.idx)
                self.idx += 1
            else:
                # Unicode escape sequence
                msg = "Invalid \\uXXXX escape sequence"
                esc = string[self.idx + 1:self.idx + 5]
                esc_x = esc[1:2]
                if len(esc) != 4 or esc_x == 'x' or esc_x == 'X':
                    raise JSONDecodeError(msg, string, self.idx - 1)
                try:
                    uni = int(esc, 16)
                except ValueError:
                    raise JSONDecodeError(msg, string, self.idx - 1)
                self.idx += 5
                # Check for surrogate pair on UCS-4 systems
                # Note that this will join high/low surrogate pairs
                # but will also pass unpaired surrogates through
                if _maxunicode > 65535 and uni & 0xfc00 == 0xd800 and string[self.idx:self.idx + 2] == '\\u':
                    esc2 = string[self.idx + 2:self.idx + 6]
                    esc_x = esc2[1:2]
                    if len(esc2) == 4 and not (esc_x == 'x' or esc_x == 'X'):
                        try:
                            uni2 = int(esc2, 16)
                        except ValueError:
                            raise JSONDecodeError(msg, string, self.idx)
                        if uni2 & 0xfc00 == 0xdc00:
                            uni = 0x10000 + (((uni - 0xd800) << 10) |
                                             (uni2 - 0xdc00))
                            self.idx += 6
                char = unichr(uni)
            # Append the unescaped character
            _append(char)
        return _join(chunks)

    def parse_object(self, string,
                     _w=WHITESPACE.match, _ws=WHITESPACE_STR):
        # Backwards compatibility
        memo_get = self.memo.setdefault
        pairs = []
        # Use a slice to prevent IndexError from being raised, the following
        # check will raise a more specific ValueError if the string is empty
        nextchar = string[self.idx:self.idx + 1]
        # Normally we expect nextchar == '"'
        if nextchar != '"':
            if nextchar in _ws:
                self.idx = _w(string, self.idx).end()
                nextchar = string[self.idx:self.idx + 1]
            # Trivial empty object
            if nextchar == '}':
                self.idx += 1
                return AttributedDict(pairs)
            elif nextchar != '"':
                raise JSONDecodeError(
                    "Expecting property name enclosed in double quotes",
                    string, self.idx)
        self.idx += 1
        while True:
            key = self.parse_string(string)
            key = memo_get(key, key)

            # To skip some function call overhead we optimize the fast paths where
            # the JSON key separator is ": " or just ":".
            if string[self.idx:self.idx + 1] != ':':
                self.idx = _w(string, self.idx).end()
                if string[self.idx:self.idx + 1] != ':':
                    raise JSONDecodeError("Expecting ':' delimiter", string, self.idx)

            self.idx += 1

            try:
                if string[self.idx] in _ws:
                    self.idx += 1
                    if string[self.idx] in _ws:
                        self.idx = _w(string, self.idx + 1).end()
            except IndexError:
                pass

            value = self.scan(string)
            pairs.append((key, value))

            try:
                nextchar = string[self.idx]
                if nextchar in _ws:
                    self.idx = _w(string, self.idx + 1).end()
                    nextchar = string[self.idx]
            except IndexError:
                nextchar = ''
            self.idx += 1

            if nextchar == '}':
                break
            elif nextchar != ',':
                raise JSONDecodeError("Expecting ',' delimiter or '}'", string, self.idx - 1)

            try:
                nextchar = string[self.idx]
                if nextchar in _ws:
                    self.idx += 1
                    nextchar = string[self.idx]
                    if nextchar in _ws:
                        self.idx = _w(string, self.idx + 1).end()
                        nextchar = string[self.idx]
            except IndexError:
                nextchar = ''

            self.idx += 1
            if nextchar != '"':
                raise JSONDecodeError(
                    "Expecting property name enclosed in double quotes",
                    string, self.idx - 1)

        return AttributedDict(pairs)

    def parse_array(self, string, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
        values = []
        nextchar = string[self.idx:self.idx + 1]
        if nextchar in _ws:
            self.idx = _w(string, self.idx + 1).end()
            nextchar = string[self.idx:self.idx + 1]
        # Look-ahead for trivial empty array
        if nextchar == ']':
            self.idx += 1
            return values
        elif nextchar == '':
            raise JSONDecodeError("Expecting value or ']'", string, self.idx)
        _append = values.append
        while True:
            value = self.scan(string)
            _append(value)
            nextchar = string[self.idx:self.idx + 1]
            if nextchar in _ws:
                self.idx = _w(string, self.idx + 1).end()
                nextchar = string[self.idx:self.idx + 1]
            self.idx += 1
            if nextchar == ']':
                break
            elif nextchar != ',':
                raise JSONDecodeError("Expecting ',' delimiter or ']'", string, self.idx - 1)

            try:
                if string[self.idx] in _ws:
                    self.idx += 1
                    if string[self.idx] in _ws:
                        self.idx = _w(string, self.idx + 1).end()
            except IndexError:
                pass

        return values

    def decode(self):
        """Return the Python representation of ``s`` (a ``str`` or ``unicode``
        instance containing a JSON document)
        """
        s = self.content
        if not PY2 and isinstance(s, binary_type):
            s = s.decode(self.encoding)
        self.idx = WHITESPACE.match(s).end()
        obj = self.scan(s)
        end = WHITESPACE.match(s, self.idx).end()
        if end != len(s):
            raise JSONDecodeError("Extra data", s, end, len(s))
        return obj

    def raw_decode(self):
        """Decode a JSON document from ``s`` (a ``str`` or ``unicode``
        beginning with a JSON document) and return a 2-tuple of the Python
        representation and the index in ``s`` where the document ended.
        Optionally, ``idx`` can be used to specify an offset in ``s`` where
        the JSON document begins.

        This can be used to decode a JSON document from a string that may
        have extraneous data at the end.

        """
        s = self.content
        if not PY2 and not isinstance(s, text_type):
            raise TypeError("Input string must be text, not bytes")
        self.idx = WHITESPACE.match(s).end()
        return self.scan(s), self.idx
