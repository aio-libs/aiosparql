from aiohttp import web
import json
from textwrap import dedent
import unittest

from aiosparql.client import SPARQLQueryFormatter
from aiosparql.syntax import IRI, RDF, Triples
from aiosparql.test_utils import AioSPARQLTestCase, unittest_run_loop


async def sparql_endpoint(request):
    result = {
        "post": dict((await request.post()).items()),
        "path": request.path,
    }
    return web.Response(text=json.dumps(result),
                        content_type="application/json")


class Client(AioSPARQLTestCase):
    client_kwargs = {
        "endpoint": "/sparql",
        "update_endpoint": "/sparql-update",
        "graph": IRI("http://mu.semte.ch/test-application"),
    }

    async def get_application(self):
        app = web.Application()
        app.router.add_post('/sparql', sparql_endpoint)
        app.router.add_post('/sparql-update', sparql_endpoint)
        return app

    @unittest_run_loop
    async def test_query(self):
        triples = Triples([("john", RDF.type, "doe"), ("john", "p", "o")])
        res = await self.client.query("""
            SELECT *
            FROM {{graph}}
            WHERE {
                {{}}
            }
            """, triples)
        self.assertEqual(res['path'], self.client_kwargs['endpoint'])
        self.assertIn('post', res)
        self.assertIn('query', res['post'])
        self.assertEqual(res['post']['query'], dedent("""\
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT *
            FROM <http://mu.semte.ch/test-application>
            WHERE {
                john rdf:type "doe" ;
                    p "o" .
            }"""))

    @unittest_run_loop
    async def test_update(self):
        triples = Triples([("john", RDF.type, "doe"), ("john", "p", "o")])
        res = await self.client.update("""
            WITH {{graph}}
            INSERT DATA {
                {{}}
            }
            """, triples)
        self.assertEqual(res['path'], self.client_kwargs['update_endpoint'])
        self.assertIn('post', res)
        self.assertIn('update', res['post'])
        self.assertEqual(res['post']['update'], dedent("""\
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            WITH <http://mu.semte.ch/test-application>
            INSERT DATA {
                john rdf:type "doe" ;
                    p "o" .
            }"""))


class Formatter(unittest.TestCase):
    formatter = SPARQLQueryFormatter()

    def _format(self, string, *args, **kwargs):
        return self.formatter.vformat(string, args, kwargs)

    def test_formatter(self):
        self.assertEqual(self._format("a\n  {{}}\nd", "b\nc"),
                         "a\n  b\n  c\nd")
        self.assertEqual(self._format("a\n{{}}\nd", "b\nc"), "a\nb\nc\nd")
        self.assertEqual(self._format("a{{}}d", "bc"), "abcd")
