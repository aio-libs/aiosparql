import pytest


sample_data = """\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix ex: <http://example.org/stuff/1.0/> .

<http://www.w3.org/TR/rdf-syntax-grammar>
  dc:title "RDF/XML Syntax Specification (Revised)" ;
  ex:editor [
    ex:fullname "Dave Beckett";
    ex:homePage <http://purl.org/net/dajobe/>
  ] .
"""

sample_format = "text/turtle"


@pytest.mark.asyncio
async def test_crud(client):
    await client.put(sample_data, format=sample_format)
    await client.delete()
    await client.post(sample_data, format=sample_format)
    async with client.get(format="text/turtle") as res:
        assert res.status == 200
        text = await res.text()
        assert "@prefix" in text


@pytest.mark.asyncio
async def test_update(client):
    update_query = """
    INSERT DATA {
        GRAPH <urn:sparql:tests:insert:data> {
        <#book1> <#price> 42
        }
    }
    """

    await client.update(update_query)
    select_query = """
    SELECT *
    FROM <urn:sparql:tests:insert:data>
    WHERE {
        ?s ?p ?o
    }
    """

    result = await client.query(select_query)
    assert len(result['results']['bindings']) == 1
