from aiohttp.test_utils import (
    AioHTTPTestCase, BaseTestServer, TestServer, unittest_run_loop)
from aiosparql.client import SPARQLClient
from aiosparql.syntax import IRI


__all__ = ['unittest_run_loop', 'AioSPARQLTestCase', 'TestSPARQLClient']


class TestSPARQLClient:
    def __init__(self, server, *, cookie_jar=None, loop=None, **kwargs):
        if not isinstance(server, BaseTestServer):
            raise TypeError("server must be web.Application TestServer "
                            "instance, found type: %r" % type(server))
        self._server = server
        self._loop = loop
        self._client_kwargs = kwargs
        self._session = None
        self._closed = False

    async def start_server(self):
        await self._server.start_server(loop=self._loop)
        kwargs = dict(self._client_kwargs)
        if kwargs.get('endpoint'):
            kwargs['endpoint'] = self.make_url(kwargs['endpoint'])
        if kwargs.get('update_endpoint'):
            kwargs['update_endpoint'] = \
                self.make_url(kwargs['update_endpoint'])
        if kwargs.get('crud_endpoint'):
            kwargs['crud_endpoint'] = self.make_url(kwargs['crud_endpoint'])
        self._session = SPARQLClient(loop=self._loop,
                                     **kwargs)

    @property
    def host(self):
        return self._server.host  # pragma nocover

    @property
    def port(self):
        return self._server.port  # pragma nocover

    @property
    def server(self):
        return self._server  # pragma nocover

    @property
    def session(self):
        if self._session is None:
            raise RuntimeError("Trying to access SPARQLClient before the "
                               "server has started")  # pragma nocover
        return self._session

    def make_url(self, path):
        return str(self._server.make_url(path))

    def query(self, query, *args, **keywords):
        return self.session.query(query, *args, **keywords)

    def update(self, query, *args, **keywords):
        return self.session.update(query, *args, **keywords)

    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.session.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.session.delete(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    async def close(self):
        if not self._closed:
            await self._session.close()
            await self._server.close()
            self._closed = True


class AioSPARQLTestCase(AioHTTPTestCase):
    client_kwargs = {
        "endpoint": "/sparql",
        "graph": IRI("http://mu.semte.ch/test-application"),
    }

    async def get_client(self, server):
        return TestSPARQLClient(server, loop=self.loop, **self.client_kwargs)
