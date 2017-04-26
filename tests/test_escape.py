import datetime
from decimal import Decimal
import unittest

from aiosparql.escape import (
    escape_any, escape_boolean, escape_date, escape_datetime, escape_float,
    escape_time, escape_string)
from aiosparql.syntax import Node, RDFTerm


class Escape(unittest.TestCase):
    def test_escape_any(self):
        now = datetime.datetime.now()
        self.assertEqual(escape_any('foo\n\r\\bar'), r'"foo\n\r\\bar"')
        self.assertEqual(escape_any(now),
                         '"%s"^^xsd:dateTime' % now.isoformat())
        self.assertEqual(escape_any(now.date()),
                         '"%s"^^xsd:date' % now.date().isoformat())
        self.assertEqual(escape_any(now.time()),
                         '"%s"^^xsd:time' % now.time().isoformat())
        self.assertEqual(escape_any(True), 'true')
        self.assertEqual(escape_any(5), '5')
        self.assertEqual(escape_any(Decimal(5.5)), '5.5')
        self.assertEqual(escape_any(5.5), '"5.5"^^xsd:double')
        self.assertEqual(escape_any(RDFTerm("raw")), 'raw')
        self.assertEqual(escape_any(Node("subject", {})), 'subject')
        with self.assertRaises(TypeError):
            escape_any(int)

    def test_escape_boolean(self):
        self.assertEqual(escape_boolean(True), 'true')
        self.assertEqual(escape_boolean(False), 'false')
        self.assertEqual(escape_boolean(1), 'true')
        self.assertEqual(escape_boolean(None), 'false')

    def test_escape_date(self):
        now = datetime.date.today()
        self.assertEqual(escape_date(now),
                         '"%s"^^xsd:date' % now.isoformat())

    def test_escape_datetime(self):
        now = datetime.datetime.now()
        self.assertEqual(escape_datetime(now),
                         '"%s"^^xsd:dateTime' % now.isoformat())

    def test_escape_float(self):
        self.assertEqual(escape_float(5.5), '"5.5"^^xsd:double')

    def test_escape_time(self):
        now = datetime.time(11, 58)
        self.assertEqual(escape_time(now),
                         '"%s"^^xsd:time' % now.isoformat())

    def _test_escape_string(self, string, expected):
        result = escape_string(string)
        self.assertEqual(result, expected)

    def test_escape_string(self):
        self._test_escape_string('foo', '"foo"')
        self._test_escape_string('foo\n\rbar', r'"foo\n\rbar"')
        self._test_escape_string('foo "bar"', r'"foo \"bar\""')
        self._test_escape_string('foo\\bar', r'"foo\\bar"')
