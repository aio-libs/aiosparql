import uuid
import pytest
import aiohttp
from os import environ as ENV

from aiosparql.client import SPARQLClient
from aiosparql.syntax import IRI


pytest_plugins = ['aiohttp.pytest_plugin', 'pytester']


@pytest.fixture
def virtuoso_client(loop):
    _virtuoso_client = SPARQLClient(
        "http://localhost:8890/sparql",
        update_endpoint=ENV.get("SPARQL_UPDATE_ENDPOINT"),
        crud_endpoint="http://localhost:8890/sparql-graph-crud",
        graph=IRI("http://aiosparql.org/%s" % uuid.uuid4().hex[:7])
    )
    yield _virtuoso_client
    try:
        loop.run_until_complete(_virtuoso_client.delete())
    except aiohttp.ClientResponseError as exc:
        if exc.status != 404:
            raise
    loop.run_until_complete(_virtuoso_client.close())


@pytest.fixture
def jena_client(loop):
    _jena_client = SPARQLClient("http://localhost:3030/ds")
    yield _jena_client
    loop.run_until_complete(_jena_client.close())


@pytest.fixture
async def truncate_jena(jena_client):
    await jena_client.update(
        """
        DELETE
        WHERE {
          GRAPH <urn:x-arq:DefaultGraph> {
            ?s ?p ?o
          }
        }
        """
    )
