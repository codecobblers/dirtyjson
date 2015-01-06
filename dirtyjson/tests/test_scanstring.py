import sys
from unittest import TestCase

import dirtyjson
import dirtyjson.decoder
from dirtyjson.compat import PY2


class TestScanString(TestCase):
    # The bytes type is intentionally not used in most of these tests
    # under Python 3 because the decoder immediately coerces to str before
    # calling scanstring. In Python 2 we are testing the code paths
    # for both unicode and str.
    #
    # The reason this is done is because Python 3 would require
    # entirely different code paths for parsing bytes and str.
    #
    def test_scanstring(self):
        decoder = dirtyjson.decoder.JSONDecoder()
        scanstring = decoder.parse_string
        if sys.maxunicode == 65535:
            self.assertEqual(
                scanstring(u'"z\U0001d120x"', 1),
                (u'z\U0001d120x', 6))
        else:
            self.assertEqual(
                scanstring(u'"z\U0001d120x"', 1),
                (u'z\U0001d120x', 5))

        self.assertEqual(
            scanstring('"\\u007b"', 1),
            (u'{', 8))

        self.assertEqual(
            scanstring('"A JSON payload should be an object or array, not a string."', 1),
            (u'A JSON payload should be an object or array, not a string.', 60))

        self.assertEqual(
            scanstring('["Unclosed array"', 2),
            (u'Unclosed array', 17))

        self.assertEqual(
            scanstring('["extra comma",]', 2),
            (u'extra comma', 14))

        self.assertEqual(
            scanstring('["double extra comma",,]', 2),
            (u'double extra comma', 21))

        self.assertEqual(
            scanstring('["Comma after the close"],', 2),
            (u'Comma after the close', 24))

        self.assertEqual(
            scanstring('["Extra close"]]', 2),
            (u'Extra close', 14))

        self.assertEqual(
            scanstring('{"Extra comma": true,}', 2),
            (u'Extra comma', 14))

        self.assertEqual(
            scanstring('{"Extra value after close": true} "misplaced quoted value"', 2),
            (u'Extra value after close', 26))

        self.assertEqual(
            scanstring('{"Illegal expression": 1 + 2}', 2),
            (u'Illegal expression', 21))

        self.assertEqual(
            scanstring('{"Illegal invocation": alert()}', 2),
            (u'Illegal invocation', 21))

        self.assertEqual(
            scanstring('{"Numbers cannot have leading zeroes": 013}', 2),
            (u'Numbers cannot have leading zeroes', 37))

        self.assertEqual(
            scanstring('{"Numbers cannot be hex": 0x14}', 2),
            (u'Numbers cannot be hex', 24))

        self.assertEqual(
            scanstring('[[[[[[[[[[[[[[[[[[[["Too deep"]]]]]]]]]]]]]]]]]]]]', 21),
            (u'Too deep', 30))

        self.assertEqual(
            scanstring('{"Missing colon" null}', 2),
            (u'Missing colon', 16))

        self.assertEqual(
            scanstring('{"Double colon":: null}', 2),
            (u'Double colon', 15))

        self.assertEqual(
            scanstring('{"Comma instead of colon", null}', 2),
            (u'Comma instead of colon', 25))

        self.assertEqual(
            scanstring('["Colon instead of comma": false]', 2),
            (u'Colon instead of comma', 25))

        self.assertEqual(
            scanstring('["Bad value", truth]', 2),
            (u'Bad value', 12))

        for c in map(chr, range(0x00, 0x1f)):
            self.assertEqual(
                scanstring(c + '"', 0),
                (c, 2))

        self.assertRaises(ValueError, scanstring, '', 0)
        self.assertRaises(ValueError, scanstring, 'a', 0)
        self.assertRaises(ValueError, scanstring, '\\', 0)
        self.assertRaises(ValueError, scanstring, '\\u', 0)
        self.assertRaises(ValueError, scanstring, '\\u0', 0)
        self.assertRaises(ValueError, scanstring, '\\u01', 0)
        self.assertRaises(ValueError, scanstring, '\\u012', 0)
        self.assertRaises(ValueError, scanstring, '\\u0123', 0)
        if sys.maxunicode > 65535:
            self.assertRaises(ValueError,
                              scanstring, '\\ud834\\u"', 0)
            self.assertRaises(ValueError,
                              scanstring, '\\ud834\\x0123"', 0)

    def test_overflow(self):
        decoder = dirtyjson.decoder.JSONDecoder()
        scanstring = decoder.parse_string
        # Python 2.5 does not have maxsize, Python 3 does not have maxint
        maxsize = getattr(sys, 'maxsize', getattr(sys, 'maxint', None))
        assert maxsize is not None
        self.assertRaises(OverflowError, scanstring, "xxx",
                          maxsize + 1)

    def test_surrogates(self):
        decoder = dirtyjson.decoder.JSONDecoder()
        scanstring = decoder.parse_string

        # noinspection PyPep8Naming
        def assertScan(given, expect, test_utf8=True):
            givens = [given]
            if PY2 and test_utf8:
                givens.append(given.encode('utf8'))
            for given in givens:
                (res, count) = scanstring(given, 1)
                self.assertEqual(len(given), count)
                self.assertEqual(res, expect)

        assertScan(
            u'"z\\ud834\\u0079x"',
            u'z\ud834yx')
        assertScan(
            u'"z\\ud834\\udd20x"',
            u'z\U0001d120x')
        assertScan(
            u'"z\\ud834\\ud834\\udd20x"',
            u'z\ud834\U0001d120x')
        assertScan(
            u'"z\\ud834x"',
            u'z\ud834x')
        assertScan(
            u'"z\\udd20x"',
            u'z\udd20x')
        assertScan(
            u'"z\ud834x"',
            u'z\ud834x')
        # It may look strange to join strings together, but Python is drunk.
        # https://gist.github.com/etrepum/5538443
        assertScan(
            u'"z\\ud834\udd20x12345"',
            u''.join([u'z\ud834', u'\udd20x12345']))
        assertScan(
            u'"z\ud834\\udd20x"',
            u''.join([u'z\ud834', u'\udd20x']))
        # these have different behavior given UTF8 input, because the surrogate
        # pair may be joined (in maxunicode > 65535 builds)
        assertScan(
            u''.join([u'"z\ud834', u'\udd20x"']),
            u''.join([u'z\ud834', u'\udd20x']),
            test_utf8=False)

        self.assertRaises(ValueError,
                          scanstring, u'"z\\ud83x"', 1)
        self.assertRaises(ValueError,
                          scanstring, u'"z\\ud834\\udd2x"', 1)
