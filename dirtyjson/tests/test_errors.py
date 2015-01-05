import sys
from unittest import TestCase

import dirtyjson
from dirtyjson.compat import u, b


class TestErrors(TestCase):
    def test_decode_error(self):
        try:
            dirtyjson.loads('{}\na\nb')
        except dirtyjson.JSONDecodeError:
            err = sys.exc_info()[1]
        else:
            self.fail('Expected JSONDecodeError')
        self.assertEqual(err.lineno, 2)
        self.assertEqual(err.colno, 1)
        self.assertEqual(err.endlineno, 3)
        self.assertEqual(err.endcolno, 2)

    def test_scan_error(self):
        for t in (u, b):
            try:
                dirtyjson.loads(t('{"asdf": "'))
            except dirtyjson.JSONDecodeError:
                err = sys.exc_info()[1]
            else:
                self.fail('Expected JSONDecodeError')
            self.assertEqual(err.lineno, 1)
            self.assertEqual(err.colno, 10)
