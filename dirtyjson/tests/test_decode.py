from __future__ import absolute_import
import decimal
from unittest import TestCase

import dirtyjson


class TestDecode(TestCase):
    if not hasattr(TestCase, 'assertIs'):
        def assertIs(self, expr1, expr2, msg=None):
            self.assertTrue(expr1 is expr2, msg or '%r is %r' % (expr1, expr2))

    def test_decimal(self):
        rval = dirtyjson.loads('1.1', parse_float=decimal.Decimal)
        self.assertTrue(isinstance(rval, decimal.Decimal))
        self.assertEqual(rval, decimal.Decimal('1.1'))

    def test_float(self):
        rval = dirtyjson.loads('1', parse_int=float)
        self.assertTrue(isinstance(rval, float))
        self.assertEqual(rval, 1.0)

    def test_decoder_optimizations(self):
        # Several optimizations were made that skip over calls to
        # the whitespace regex, so this test is designed to try and
        # exercise the uncommon cases. The array cases are already covered.
        rval = dirtyjson.loads('{   "key"    :    "value"    ,  "k":"v"    }')
        self.assertEqual(rval, {"key": "value", "k": "v"})

    def test_empty_objects(self):
        s = '{}'
        self.assertEqual(dirtyjson.loads(s), eval(s))
        s = '[]'
        self.assertEqual(dirtyjson.loads(s), eval(s))
        s = '""'
        self.assertEqual(dirtyjson.loads(s), eval(s))

    def check_keys_reuse(self, source, loads):
        rval = loads(source)
        (a, b), (c, d) = sorted(rval[0]), sorted(rval[1])
        self.assertIs(a, c)
        self.assertIs(b, d)

    def test_keys_reuse_str(self):
        s = u'[{"a_key": 1, "b_\xe9": 2}, {"a_key": 3, "b_\xe9": 4}]'.encode('utf8')
        self.check_keys_reuse(s, dirtyjson.loads)

    def test_keys_reuse_unicode(self):
        s = u'[{"a_key": 1, "b_\xe9": 2}, {"a_key": 3, "b_\xe9": 4}]'
        self.check_keys_reuse(s, dirtyjson.loads)

    def test_empty_strings(self):
        self.assertEqual(dirtyjson.loads('""'), "")
        self.assertEqual(dirtyjson.loads(u'""'), u"")
        self.assertEqual(dirtyjson.loads('[""]'), [""])
        self.assertEqual(dirtyjson.loads(u'[""]'), [u""])

    def test_raw_decode(self):
        cls = dirtyjson.JSONDecoder
        self.assertEqual(
            ({'a': {}}, 9),
            cls().raw_decode("{\"a\": {}}"))
        # http://code.google.com/p/dirtyjson/issues/detail?id=85
        self.assertEqual(
            ({'a': {}}, 9),
            cls().raw_decode("{\"a\": {}}"))
        # https://github.com/dirtyjson/dirtyjson/pull/38
        self.assertEqual(
            ({'a': {}}, 11),
            cls().raw_decode(" \n{\"a\": {}}"))
