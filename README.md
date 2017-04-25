[![Build Status](https://travis-ci.org/tenforce/sparql-aiohttp.svg?branch=master)](https://travis-ci.org/tenforce/sparql-aiohttp)
[![codecov](https://codecov.io/gh/tenforce/sparql-aiohttp/branch/master/graph/badge.svg)](https://codecov.io/gh/tenforce/sparql-aiohttp)

An asynchronous SPARQL library using aiohttp
============================================

Synopsis
--------

```python
from aiosparql.syntax import (
    IRI, Namespace, Node, PrefixedName, RDF, RDFTerm, Triples)

# define a namespace

class Boo(Namespace):
    __iri__ = IRI("http://boo#")
    SomeClass = PrefixedName
    website = PrefixedName
    label = PrefixedName

# create a node

node = Node("<subject>", {
    RDF.type: Boo.SomeClass,
    Boo.website: IRI("http://example.org"),
    Boo.label: "some label", # "some label" will be automatically escaped
})

# missing prefixed names will show on your IDE and fail on execution

print(Boo.something) # AttributeError!

# create triples

triples = Triples([("s", "p", "o")]) # o is automatically escaped
triples.append(("s", Boo.website, IRI("http://example.org")))
triples.extend([("s", Boo.website, IRI("http://example.org"))])

print(triples) # print the triples is a format usable directly in a SPARQL
               # query. It also groups by subject automatically for you


from aiosparql.client import SPARQLClient

client = SPARQLClient("http://dbpedia.org/sparql")
result = await client.query("select * where {?s ?p ?o} limit 1")
# result is a dict of the JSON result
result = await client.update("""
    with {{graph}}
    insert data {
        {{}}
    }
    """, triples)
# the triples will be automatically indented to produce a beautiful query


from aiosparql.escape import escape_any

print(escape_any(True)) # "true"
print(escape_any("foo")) # "foo"
print(escape_any(5)) # "5"
print(escape_any(5.5)) # "5.5"^^xsd:double
```

Installation
------------

 *  User space installation

    ```
    easy_install --user aiosparql
    ```

 *  System wide installation

    ```
    easy_install aiosparql
    ```

### Requirements

 *  Python >= 3.5
