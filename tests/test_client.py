import unittest

from aiosparql.client import SPARQLQueryFormatter


class Client(unittest.TestCase):
    formatter = SPARQLQueryFormatter()

    def _format(self, string, *args, **kwargs):
        return self.formatter.vformat(string, args, kwargs)

    def test_formatter(self):
        self.assertEqual(self._format("a\n  {{}}\nd", "b\nc"),
                         "a\n  b\n  c\nd")
        self.assertEqual(self._format("a\n{{}}\nd", "b\nc"), "a\nb\nc\nd")
        self.assertEqual(self._format("a{{}}d", "bc"), "abcd")
