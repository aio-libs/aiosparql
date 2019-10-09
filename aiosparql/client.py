import aiohttp
import asyncio
import logging
import re
from io import IOBase
from math import ceil, log10
from string import Formatter
from textwrap import dedent, indent
from typing import Dict, Optional, Union

from .syntax import IRI, all_prefixes

__all__ = ['SPARQLClient', 'SPARQLRequestFailed', 'SPARQLQueryFormatter']


logger = logging.getLogger(__name__)


class SPARQLRequestFailed(aiohttp.client_exceptions.ClientResponseError):
    def __init__(self, request_info, history, *,
                 code=0, message='', headers=None, explanation=None):
        super(SPARQLRequestFailed, self).__init__(
            request_info, history, code=code, message=message, headers=headers)
        self.explanation = explanation

    def __str__(self):
        base_message = super(SPARQLRequestFailed, self).__str__()
        return "%s, explanation=%r" % (base_message, self.explanation)


class SPARQLQueryFormatter(Formatter):
    """
    This custom formatter redefine the parse method of the default Python's
    formatter in order to use {{}} instead of {} as replacement field.

    It also automatically indents text, example:
    s = "\n".join(["b", "c", "d"])
    SPARQLQueryFormatter().vformat("a\n  {{}}\ne", [s], {})
    # returns:
    # a
    #     b
    #     c
    #     d
    # e
    """
    re_token = \
        re.compile(r"((?:[^{]+|\{[^{]+|\{$)*)(?:\{\{((?:[^}]+|}[^}])*)\}\})?")
    re_field = re.compile(r"(.*)(?:!([sra]))?(?::([^{}]*))?")
    re_indent = re.compile(r"(.*)^(\s*)$", flags=(re.M + re.S))
    indent = ""

    def parse(self, s):
        if not s:
            return
        else:
            for match in self.re_token.finditer(s):
                imatch = self.re_indent.fullmatch(match.group(1))
                if imatch:
                    text = imatch.group(1)
                    self.indent = imatch.group(2)
                else:
                    text = match.group(1)
                    self.indent = ""
                if match.group(2) is None:
                    if match.end() != len(s):
                        raise Exception(
                            "Not terminated token: %r" % s[match.end():])
                    yield (text, None, None, None)
                    break
                else:
                    fmatch = self.re_field.fullmatch(match.group(2))
                    if not fmatch:
                        raise Exception(
                            "Cannot parse token: %r" % match.group(2))
                    yield (text, fmatch.group(1), fmatch.group(3),
                           fmatch.group(2))

    def format_field(self, value, format_spec):
        return indent(format(value, format_spec), self.indent)


class SPARQLClient:
    def __init__(self, endpoint: str, *,
                 update_endpoint: Optional[str] = None,
                 crud_endpoint: Optional[str] = None,
                 prefixes: Optional[Dict[str, IRI]] = None,
                 graph: Optional[IRI] = None,
                 **kwargs):
        self._closed = False
        self._endpoint = endpoint
        self._update_endpoint = update_endpoint
        self._crud_endpoint = crud_endpoint
        self._graph = graph
        self.session = aiohttp.ClientSession(**kwargs)
        self._generate_prefixes(prefixes)

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def update_endpoint(self):
        return self._update_endpoint or self._endpoint

    @property
    def crud_endpoint(self):
        return self._crud_endpoint

    @property
    def graph(self):
        return self._graph

    def _generate_prefixes(self, prefixes):
        header = [
            "PREFIX %s: %s" % (prefix, ns.__iri__)
            for prefix, ns in sorted(all_prefixes.items(), key=lambda x: x[0])
        ]
        if prefixes:
            header.append("")
            header.extend([
                "PREFIX %s: %s" % x
                for x in sorted(prefixes.items(), key=lambda x: x[0])
            ])
        self._prefixes_header = "\n".join(header) + "\n"

    def _prepare_query(self, query: str, *args, **keywords) -> dict:
        lines = [self._prefixes_header]
        lines.extend([dedent(query).strip()])
        query_args = {'graph': self.graph} if self.graph else {}
        query_args.update(keywords)
        query_formatter = SPARQLQueryFormatter()
        return query_formatter.vformat("\n".join(lines), args, query_args)

    def _pretty_print_query(self, query: str) -> str:
        query = query.rstrip()
        ln_indent = ceil(log10(query.count("\n")))
        return "\n".join(
            ("{:-%dd}: {}" % ln_indent).format(i, x)
            for i, x in enumerate(query.split("\n"), 1)
        )

    async def _raise_for_status(self, resp: aiohttp.ClientResponse) -> None:
        if resp.status >= 400:
            explanation = await resp.text()
            resp.release()
            logger.debug("Server responded:\n%s\n%s",
                         explanation, "=" * 40)
            raise SPARQLRequestFailed(
                resp.request_info, resp.history,
                code=resp.status, message=resp.reason,
                explanation=explanation)

    async def query(self, query: str, *args, **keywords) -> dict:
        headers = {
            "Accept": "application/json",
        }
        full_query = self._prepare_query(query, *args, **keywords)
        logger.debug("Sending SPARQL query to %s: \n%s\n%s",
                     self.endpoint, self._pretty_print_query(full_query),
                     "=" * 40)
        async with self.session.post(self.endpoint, data={"query": full_query},
                                     headers=headers) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def update(self, query: str, *args, **keywords) -> dict:
        headers = {
            "Accept": "application/json",
        }
        full_query = self._prepare_query(query, *args, **keywords)
        logger.debug("Sending SPARQL query to %s:\n%s\n%s",
                     self.endpoint, self._pretty_print_query(full_query),
                     "=" * 40)
        async with self.session.post(self.update_endpoint,
                                     data={"update": full_query},
                                     headers=headers) as resp:
            await self._raise_for_status(resp)
            # NOTE: some databases may still return HTML instead of JSON
            if "application/json" not in resp.content_type:
                return {
                    "body": await resp.text(),
                }
            return await resp.json()

    def _crud_request(self, method, graph=None, data=None, accept=None,
                      content_type=None):
        if not self.crud_endpoint:
            raise ValueError("CRUD endpoint not specified")
        url = self.crud_endpoint
        if graph:
            params = {'graph': graph.value}
        elif self.graph:
            params = {'graph': self.graph.value}
        else:
            params = None
            url += "?default"
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        if accept:
            headers["Accept"] = accept
        logger.debug("Sending %s request to CRUD endpoint %s with headers "
                     "%r, and params %r", method, url, headers, params)
        return self.session.request(method, url, params=params,
                                    headers=headers, data=data)

    def get(self, *, format: str, graph: Optional[IRI] = None):
        return self._crud_request("GET", graph=graph, accept=format)

    async def put(self, data: Union[bytes, IOBase], *, format: str,
                  graph: Optional[IRI] = None):
        async with self._crud_request("PUT", graph=graph, data=data,
                                      content_type=format) as resp:
            resp.raise_for_status()

    async def delete(self, graph: Optional[IRI] = None):
        async with self._crud_request("DELETE", graph=graph) as resp:
            resp.raise_for_status()

    async def post(self, data: Union[bytes, IOBase], *, format: str,
                   graph: Optional[IRI] = None):
        async with self._crud_request("POST", graph=graph, data=data,
                                      content_type=format) as resp:
            resp.raise_for_status()

    @property
    def closed(self):
        return self._closed

    @asyncio.coroutine
    def close(self):
        self._closed = True
        # NOTE: TypeError: object _CoroGuard can't be used in 'await'
        #       expression
        yield from self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
