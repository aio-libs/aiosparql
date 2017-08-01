import aiohttp
import unittest
import uuid
from aiohttp.test_utils import setup_test_loop, unittest_run_loop
from os import environ as ENV

from aiosparql.client import SPARQLClient
from aiosparql.syntax import IRI

__all__ = ['IntegrationTestCase', 'unittest_run_loop']


class IntegrationTestCase(unittest.TestCase):
    async def _create_client(self):
        return SPARQLClient(
            ENV.get("SPARQL_ENDPOINT", "http://localhost:8890/sparql"),
            update_endpoint=ENV.get("SPARQL_UPDATE_ENDPOINT"),
            crud_endpoint=ENV.get("SPARQL_UPDATE_ENDPOINT",
                                  "http://localhost:8890/sparql-graph-crud"),
            graph=self.graph)

    def _generate_random_graph(self):
        return IRI("http://aiosparql.org/%s" % uuid.uuid4().hex[:7])

    def setUp(self):
        self.loop = setup_test_loop()
        self.graph = self._generate_random_graph()
        self.client = self.loop.run_until_complete(self._create_client())

    def tearDown(self):
        try:
            self.loop.run_until_complete(self.client.delete())
        except aiohttp.ClientResponseError as exc:
            if exc.code != 404:
                raise
        self.loop.run_until_complete(self.client.close())
        self.loop.close()
