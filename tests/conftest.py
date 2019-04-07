import aiohttp
import uuid
import pytest
from os import environ as ENV

from aiosparql.client import SPARQLClient
from aiosparql.test_utils import AioSPARQLTestCase
from aiosparql.syntax import IRI


pytest_plugins = ['aiohttp.pytest_plugin', 'pytester']


@pytest.fixture
async def client(loop):
    client = SPARQLClient(
        ENV.get("SPARQL_ENDPOINT", "http://localhost:8890/sparql"),
        update_endpoint=ENV.get("SPARQL_UPDATE_ENDPOINT"),
        crud_endpoint=ENV.get(
            "SPARQL_UPDATE_ENDPOINT",
            "http://localhost:8890/sparql-graph-crud"
        ),
        graph=IRI("http://aiosparql.org/%s" % uuid.uuid4().hex[:7])
    )
    yield client
    try:
        await client.delete()
    except aiohttp.ClientResponseError as exc:
        if exc.status != 404:
            raise
    await client.close()


@pytest.fixture
def test_client():
    return AioSPARQLTestCase()
