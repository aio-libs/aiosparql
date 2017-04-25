from aiohttp.test_utils import AioHTTPTestCase, TestClient, unittest_run_loop
from aiosparql.client import SPARQLClient
from aiosparql.syntax import IRI
import asyncio


__all__ = ['unittest_run_loop', 'AioSPARQLTestCase', 'TestSPARQLClient']


class TestSPARQLClient(TestClient, SPARQLClient):
    def __init__(self, app, **kwargs):
        TestClient.__init__(self, app, loop=kwargs.get('loop'))
        SPARQLClient.__init__(self, **kwargs)


class AioSPARQLTestCase(AioHTTPTestCase):
    client_kwargs = {
        "endpoint": "/sparql",
        "graph": IRI("http://mu.semte.ch/test-application"),
    }

    @asyncio.coroutine
    def _get_client(self, app):
        return TestSPARQLClient(self.app, loop=self.loop, **self.client_kwargs)
