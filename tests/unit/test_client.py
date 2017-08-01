import aiohttp
import json
import unittest
from aiohttp import web
from textwrap import dedent

from aiosparql.client import (
    SPARQLClient, SPARQLQueryFormatter, SPARQLRequestFailed)
from aiosparql.syntax import IRI, RDF, Triples
from aiosparql.test_utils import AioSPARQLTestCase, unittest_run_loop


async def sparql_endpoint(request):
    result = {
        "post": dict((await request.post()).items()),
        "path": request.path,
    }
    if "failure" in result['post'].get('query', ""):
        raise web.HTTPBadRequest()
    if "failure" in result['post'].get('update', ""):
        raise web.HTTPBadRequest()
    return web.Response(text=json.dumps(result),
                        content_type="application/json")


async def crud_endpoint(request):
    request.app['last_request'] = request
    if request.method == "PATCH":
        return web.Response(text="{}", content_type="application/json")
    else:
        raise web.HTTPNoContent()


class ClientWithoutGraph(AioSPARQLTestCase):
    client_kwargs = {
        "endpoint": "/sparql",
        "crud_endpoint": "/crud",
    }

    async def get_application(self):
        app = web.Application()
        app.router.add_route('*', '/crud', crud_endpoint)
        return app

    @unittest_run_loop
    async def test_get(self):
        async with self.client.get(format="some/format") as response:
            self.assertIsInstance(response, aiohttp.ClientResponse)
        self.assertEqual(self.app['last_request'].method, "GET")
        self.assertEqual(self.app['last_request'].query_string, "default")
        self.assertEqual(self.app['last_request'].headers['Accept'],
                         "some/format")

        async with self.client.get(format="some/format", graph=IRI("foo")) \
                as response:
            self.assertIsInstance(response, aiohttp.ClientResponse)
        self.assertEqual(self.app['last_request'].method, "GET")
        self.assertEqual(self.app['last_request'].query_string, "graph=foo")
        self.assertEqual(self.app['last_request'].headers['Accept'],
                         "some/format")


class Client(AioSPARQLTestCase):
    client_kwargs = {
        "endpoint": "/sparql",
        "update_endpoint": "/sparql-update",
        "crud_endpoint": "/crud",
        "graph": IRI("http://mu.semte.ch/test-application"),
    }

    async def get_application(self):
        app = web.Application()
        app.router.add_post('/sparql', sparql_endpoint)
        app.router.add_post('/sparql-update', sparql_endpoint)
        app.router.add_route('*', '/crud', crud_endpoint)
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
        with self.assertRaises(SPARQLRequestFailed):
            await self.client.query("failure")

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
        with self.assertRaises(SPARQLRequestFailed):
            await self.client.update("failure")

    @unittest_run_loop
    async def test_get(self):
        async with self.client.get(format="some/format") as response:
            self.assertIsInstance(response, aiohttp.ClientResponse)
        self.assertEqual(self.app['last_request'].method, "GET")
        self.assertEqual(self.app['last_request'].query_string,
                         "graph=%s" % self.client_kwargs['graph'].value)
        self.assertEqual(self.app['last_request'].headers['Accept'],
                         "some/format")

        async with self.client.get(format="some/format", graph=IRI("foo")) \
                as response:
            self.assertIsInstance(response, aiohttp.ClientResponse)
        self.assertEqual(self.app['last_request'].method, "GET")
        self.assertEqual(self.app['last_request'].query_string, "graph=foo")
        self.assertEqual(self.app['last_request'].headers['Accept'],
                         "some/format")

    @unittest_run_loop
    async def test_put(self):
        await self.client.put(b"", format="some/format")
        self.assertEqual(self.app['last_request'].method, "PUT")
        self.assertEqual(self.app['last_request'].query_string,
                         "graph=%s" % self.client_kwargs['graph'].value)
        self.assertEqual(self.app['last_request'].headers['Content-Type'],
                         "some/format")

        await self.client.put(b"", format="some/format", graph=IRI("foo"))
        self.assertEqual(self.app['last_request'].query_string, "graph=foo")

    @unittest_run_loop
    async def test_delete(self):
        await self.client.delete()
        self.assertEqual(self.app['last_request'].method, "DELETE")
        self.assertEqual(self.app['last_request'].query_string,
                         "graph=%s" % self.client_kwargs['graph'].value)

        await self.client.delete(IRI("foo"))
        self.assertEqual(self.app['last_request'].query_string, "graph=foo")

    @unittest_run_loop
    async def test_post(self):
        await self.client.post(b"", format="some/format")
        self.assertEqual(self.app['last_request'].method, "POST")
        self.assertEqual(self.app['last_request'].query_string,
                         "graph=%s" % self.client_kwargs['graph'].value)
        self.assertEqual(self.app['last_request'].headers['Content-Type'],
                         "some/format")

        await self.client.post(b"", format="some/format", graph=IRI("foo"))
        self.assertEqual(self.app['last_request'].query_string, "graph=foo")


class ClientCustomPrefixes(AioSPARQLTestCase):
    client_kwargs = {
        "endpoint": "/sparql",
        "update_endpoint": "/sparql-update",
        "graph": IRI("http://mu.semte.ch/test-application"),
        "prefixes": {
            "foo": IRI("http://foo#"),
            "bar": IRI("http://bar#"),
            "baz": IRI("http://baz#"),
        },
    }

    async def get_application(self):
        app = web.Application()
        app.router.add_post('/sparql', sparql_endpoint)
        app.router.add_post('/sparql-update', sparql_endpoint)
        return app

    @unittest_run_loop
    async def test_custom_prefixes(self):
        res = await self.client.query("noop")
        self.assertEqual(res['post']['query'], dedent("""\
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            PREFIX bar: <http://bar#>
            PREFIX baz: <http://baz#>
            PREFIX foo: <http://foo#>

            noop"""))


class Formatter(unittest.TestCase):
    formatter = SPARQLQueryFormatter()

    def _format(self, string, *args, **kwargs):
        return self.formatter.vformat(string, args, kwargs)

    def test_formatter(self):
        self.assertEqual(self._format("a\n  {{}}\nd", "b\nc"),
                         "a\n  b\n  c\nd")
        self.assertEqual(self._format("a\n{{}}\nd", "b\nc"), "a\nb\nc\nd")
        self.assertEqual(self._format("a{{}}d", "bc"), "abcd")


async def test_client_context(loop):
    async with SPARQLClient(endpoint="http://example.org",
                            graph="http://example/graph") as client:
        assert not client.session.closed
        assert not client.closed
    assert client.session.closed
    assert client.closed
