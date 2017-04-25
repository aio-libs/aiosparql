from textwrap import dedent, indent
import unittest

from aiosparql.syntax import IRI, Literal, Node, RDF, Triples, UNDEF


class Syntax(unittest.TestCase):
    def test_node(self):
        node = Node("john", ([(RDF.type, "doe"), ("foo", "bar")]))
        self.assertEqual(str(node), dedent("""\
            john rdf:type "doe" ;
                foo "bar" ."""))

    def test_triples(self):
        triples = Triples([("john", RDF.type, "doe")])
        triples.append(("john", "foo", "bar"))
        triples.extend([("jane", "hello", Literal("world", "en"))])
        self.assertEqual(str(triples), dedent("""\
            john rdf:type "doe" ;
                foo "bar" .

            jane hello "world"@en ."""))
        self.assertEqual(triples.indent("  "), indent(str(triples), "  "))

    def test_iri(self):
        self.assertEqual(str(IRI("http://example.org")),
                         "<http://example.org>")

    def test_undef(self):
        self.assertEqual(str(UNDEF()), "UNDEF")
