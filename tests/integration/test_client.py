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
async def test_crud_virtuoso(virtuoso_client):
    await virtuoso_client.put(sample_data, format=sample_format)
    await virtuoso_client.delete()
    await virtuoso_client.post(sample_data, format=sample_format)
    async with virtuoso_client.get(format=sample_format) as res:
        assert res.status == 200
        text = await res.text()
        assert "@prefix" in text


@pytest.mark.asyncio
async def test_update_insert_virtuoso(virtuoso_client):
    update_query = """
    INSERT DATA {
        GRAPH <urn:sparql:tests:insert:data> {
        <#book1> <#price> 42
        }
    }
    """
    await virtuoso_client.update(update_query)
    select_query = """
    SELECT *
    FROM <urn:sparql:tests:insert:data>
    WHERE {
        ?s ?p ?o
    }
    """
    result = await virtuoso_client.query(select_query)
    assert len(result['results']['bindings']) == 1


@pytest.mark.asyncio
async def test_update_delete_virtuoso(virtuoso_client):
    update_query = """
    INSERT DATA {
        GRAPH <urn:sparql:tests:insert:data> {
        <#book1> <#price> 42
        }
    }
    """
    await virtuoso_client.update(update_query)
    delete_query = """
    WITH <urn:sparql:tests:insert:data>
    DELETE {
        ?s ?p ?o
    }
    WHERE {
        ?s ?p ?o
    }
    """
    result = await virtuoso_client.query(delete_query)
    assert len(result['results']['bindings']) == 1
    select_query = """
    SELECT *
    FROM <urn:sparql:tests:insert:data>
    WHERE {
        ?s ?p ?o
    }
    """
    result = await virtuoso_client.query(select_query)
    assert len(result['results']['bindings']) == 0


@pytest.mark.asyncio
async def test_update_delete_jena(jena_client, truncate_jena):
    update_query = """
    INSERT DATA {
        <#book1> <#price> 42
    }
    """
    await jena_client.update(update_query)
    select_query = """
    SELECT *
    WHERE {
      GRAPH <urn:x-arq:DefaultGraph> {
        ?s ?p ?o
      }
    }
    """
    result = await jena_client.query(select_query)
    assert len(result['results']['bindings']) == 1
    delete_query = """
    DELETE
    WHERE {
      GRAPH <urn:x-arq:DefaultGraph> {
        ?s ?p ?o
      }
    }
    """
    result = await jena_client.update(delete_query)
    result = await jena_client.query(select_query)
    assert len(result['results']['bindings']) == 0
