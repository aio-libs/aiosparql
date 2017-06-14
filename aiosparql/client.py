import aiohttp
from asyncio import AbstractEventLoop
import logging
from math import ceil, log10
from os import environ as ENV
import re
from string import Formatter
from textwrap import dedent, indent
from typing import List, Optional

from .syntax import IRI, MetaNamespace, Namespace

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


class SPARQLClient(aiohttp.ClientSession):
    def __init__(self,
                 endpoint: Optional[str] = None,
                 update_endpoint: Optional[str] = None,
                 prefixes: Optional[List[Namespace]] = None,
                 graph: Optional[str] = None,
                 loop: Optional[AbstractEventLoop] = None):
        super(SPARQLClient, self).__init__(loop=loop)
        self.endpoint = endpoint or ENV['MU_SPARQL_ENDPOINT']
        self.graph = graph or IRI(ENV['MU_APPLICATION_GRAPH'])
        self.update_endpoint = update_endpoint or self.endpoint
        self.prefixes = (
            MetaNamespace.prefixes.values() if prefixes is None else prefixes
        )

    def _prepare_query(self, query: str, *args, **keywords) -> dict:
        lines = [
            "PREFIX %s: %s" % (x.__prefix_label__, x.__iri__)
            for x in self.prefixes
        ]
        lines.extend(["", dedent(query).strip()])
        query_args = {
            'graph': self.graph,
        }
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

    async def query(self, query: str, *args, **keywords) -> dict:
        headers = {
            "Accept": "application/json",
        }
        full_query = self._prepare_query(query, *args, **keywords)
        logger.debug("Sending SPARQL query to %s: \n%s\n%s",
                     self.endpoint, self._pretty_print_query(full_query),
                     "=" * 40)
        async with self.post(self.endpoint, data={"query": full_query},
                             headers=headers) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.client_exceptions.ClientResponseError as exc:
                explanation = await resp.text()
                logger.debug("Server responded:\n%s\n%s",
                             explanation, "=" * 40)
                raise SPARQLRequestFailed(
                    exc.request_info, exc.history,
                    code=exc.code, message=exc.message,
                    explanation=explanation)
            return await resp.json()

    async def update(self, query: str, *args, **keywords) -> dict:
        headers = {
            "Accept": "application/json",
        }
        full_query = self._prepare_query(query, *args, **keywords)
        logger.debug("Sending SPARQL query to %s:\n%s\n%s",
                     self.endpoint, self._pretty_print_query(full_query),
                     "=" * 40)
        async with self.post(self.update_endpoint, data={"update": full_query},
                             headers=headers) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.client_exceptions.ClientResponseError as exc:
                explanation = await resp.text()
                logger.debug("Server responded:\n%s\n%s",
                             explanation, "=" * 40)
                raise SPARQLRequestFailed(
                    exc.request_info, exc.history,
                    code=exc.code, message=exc.message, headers=exc.headers,
                    explanation=explanation)
            return await resp.json()
