from tests.integration.helpers import IntegrationTestCase, unittest_run_loop


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


class Client(IntegrationTestCase):
    @unittest_run_loop
    async def test_crud(self):
        await self.client.put(sample_data, format=sample_format)
        await self.client.delete()
        await self.client.post(sample_data, format=sample_format)
        async with self.client.get(format="text/turtle") as res:
            self.assertEqual(res.status, 200)
            text = await res.text()
            self.assertIn("@prefix", text)
