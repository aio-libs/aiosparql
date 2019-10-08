from configparser import ConfigParser
import uuid
import pytest
import aiohttp
from os import environ as ENV

from aiosparql.client import SPARQLClient
from aiosparql.test_utils import AioSPARQLTestCase
from aiosparql.syntax import IRI


pytest_plugins = ['aiohttp.pytest_plugin', 'pytester']


@pytest.fixture
def config():
    cfg = ConfigParser()
    cfg.read('testing.cfg')
    yield cfg


@pytest.fixture
def jena_endpoint(config: ConfigParser):
    yield config.get('jena', 'endpoint')


@pytest.fixture
def virtuoso_endpoint(config: ConfigParser):
    yield config.get('virtuoso', 'endpoint')


@pytest.fixture
async def virtuoso_client(loop, virtuoso_endpoint):
    _virtuoso_client = SPARQLClient(
        virtuoso_endpoint,
        update_endpoint=ENV.get("SPARQL_UPDATE_ENDPOINT"),
        crud_endpoint="http://localhost:8890/sparql-graph-crud",
        graph=IRI("http://aiosparql.org/%s" % uuid.uuid4().hex[:7])
    )
    yield _virtuoso_client
    try:
        await _virtuoso_client.delete()
    except aiohttp.ClientResponseError as exc:
        if exc.status != 404:
            raise
    await _virtuoso_client.close()


@pytest.fixture
async def jena_client(loop, jena_endpoint):
    _jena_client = SPARQLClient(jena_endpoint)
    yield _jena_client
    await _jena_client.close()


@pytest.fixture
def test_client():
    return AioSPARQLTestCase()
