from itertools import groupby
import re
from textwrap import indent

from .escape import escape_any, escape_string, escapers


__all__ = [
    "RDFTerm", "Node", "Triples", "PrefixedName", "IRI", "Literal", "UNDEF",
    "Namespace", "RDF",
]


class RDFTerm:
    """
    A base class for any class that can be print (using str()) and return a
    valid RDF term (i.e. that can be used in a SPARQL query).
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, RDFTerm):
            return self.value == other.value
        else:
            return self.value == other

    def __hash__(self):
        return hash(self.value)


class Node(list):
    """
    A magical list of tuples (p, o) with a subject that can be printed to a
    SPARQL query.

    It can also accept a dict in argument.
    """
    def __init__(self, subject, value=[]):
        self.subject = subject
        if isinstance(value, dict):
            super(Node, self).__init__(value.items())
        else:
            super(Node, self).__init__(value)

    def __str__(self):
        return "".join(self._output_triples())

    def _output_triples(self):
        it = iter(sorted(self, key=self._group_key))
        p, o = next(it)
        yield "%s %s %s" % (self.subject, p, escape_any(o))
        for p, o in it:
            assert p is not None, "predicate not defined"
            if o is None:
                continue
            yield " ;\n"
            yield "    %s %s" % (p, escape_any(o))
        yield " ."

    def _group_key(self, x):
        return str(x[0])


class Triples(list):
    """
    A magical list of tuples (s, p, o) that be printed to a SPARQL query.
    """
    def __init__(self, value=[]):
        assert all(isinstance(x, (tuple, Node)) for x in value), \
            "only tuples and Node are accepted, received: %r" % value
        assert all(len(x) == 3 for x in value if isinstance(x, tuple)), \
            "tuples must be of length 3"
        return super(Triples, self).__init__(value)

    def append(self, triple):
        assert isinstance(triple, (tuple, Node)), \
            "only tuples are Node accepted, received: %r" % triple
        assert len(triple) == 3 if isinstance(triple, tuple) else True, \
            "tuple must be of length 3"
        return super(Triples, self).append(triple)

    def extend(self, value):
        assert all(isinstance(x, (tuple, Node)) for x in value), \
            "only tuples are Node accepted, received: %r" % value
        assert all(len(x) == 3 for x in value if isinstance(x, tuple)), \
            "tuples must be of length 3"
        return super(Triples, self).extend(value)

    def __str__(self):
        return "".join(self._output_triples())

    def indent(self, spaces):
        return indent(str(self), spaces)

    def _output_triples(self):
        item = None
        for s, group in groupby(self, self._group_key):
            assert s is not None, "subject not defined"
            if item is None:
                pass
            elif isinstance(item, tuple):
                yield " .\n\n"
            elif isinstance(item, Node):
                yield "\n\n"
            item = next(group)
            if isinstance(item, tuple):
                s, p, o = item
                yield "%s %s %s" % (s, p, escape_any(o))
                for _, p, o in group:
                    assert p is not None, "predicate not defined"
                    if o is None:
                        continue
                    yield " ;\n"
                    yield "    %s %s" % (p, escape_any(o))
            elif isinstance(item, Node):
                yield str(item)
        if isinstance(item, tuple):
            yield " ."

    def _group_key(self, x):
        if isinstance(x, tuple):
            return x[0]
        elif isinstance(x, Node):
            return id(x)


class PrefixedName(RDFTerm):
    def __init__(self, base_iri, prefix_label, local_part):
        self.base_iri = base_iri
        self.prefix_label = prefix_label
        self.local_part = local_part

    def __str__(self):
        return "%s:%s" % (self.prefix_label, self.local_part)

    def __repr__(self):
        return "<PrefixedName %s>" % self

    def __eq__(self, other):
        if isinstance(other, PrefixedName):
            return (self.prefix_label == other.prefix_label and
                    self.local_part == other.local_part)
        else:
            return self.iri() == other

    def __hash__(self):
        return hash(self.iri())

    def iri(self):
        return IRI(self.base_iri.value + self.local_part)


class IRI(RDFTerm):
    __re_invalid_chars__ = re.compile('[<>"{}|^`[-\\]\x00-\x20]')

    def __init__(self, value):
        self.value = value
        self.ref = "<%s>" % self.__re_invalid_chars__.sub(
            lambda x: '%{:02X}'.format(ord(x.group(0))), value)

    def __str__(self):
        return self.ref

    def __repr__(self):
        return "<IRI %s>" % self.value

    def __eq__(self, other):
        if isinstance(other, IRI):
            return self.value == other.value
        else:
            return self.value == other

    def __hash__(self):
        return hash(self.value)

    def __add__(self, other):
        return IRI("%s%s" % (self.value, other))


class Literal(RDFTerm):
    def __init__(self, value, lang=None):
        self.value = value
        self.lang = lang

    def __str__(self):
        return "%s@%s" % (escape_string(self.value), self.lang)

    def __eq__(self, other):
        if isinstance(other, Literal):
            return (self.value == other.value and self.lang == other.lang)
        else:
            return self.value == other

    def __hash__(self):
        return hash((self.value, self.lang))


class UNDEF(RDFTerm):
    def __init__(self):
        pass

    def __str__(self):
        return "UNDEF"

    def __eq__(self, other):
        return isinstance(other, UNDEF)

    def __hash__(self):
        return hash(UNDEF)


class MetaNamespace(type):
    prefixes = {}

    def __new__(mcs, name, bases, nmspc):
        if bases:
            assert '__iri__' in nmspc, \
                "missing attribute __iri__ for class %s" % name
            iri = nmspc['__iri__']
            prefix_label = nmspc.get('__prefix_label__', name.lower())
            nmspc = {
                k: (
                    PrefixedName(iri, prefix_label, k)
                    if v is PrefixedName else v
                )
                for k, v in nmspc.items()
            }
            nmspc['__prefix_label__'] = prefix_label
        return super(MetaNamespace, mcs).__new__(mcs, name, bases, nmspc)

    def __init__(cls, name, bases, nmspc):
        super(MetaNamespace, cls).__init__(name, bases, nmspc)
        if bases:
            MetaNamespace.prefixes[name] = cls


class Namespace(metaclass=MetaNamespace):
    __prefix_label__ = ""


class RDF(Namespace):
    __iri__ = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

    HTML = PrefixedName
    langString = PrefixedName
    PlainLiteral = PrefixedName
    type = PrefixedName
    Property = PrefixedName
    Statement = PrefixedName
    subject = PrefixedName
    predicate = PrefixedName
    object = PrefixedName
    Bag = PrefixedName
    Seq = PrefixedName
    Alt = PrefixedName
    value = PrefixedName
    List = PrefixedName
    nil = PrefixedName
    first = PrefixedName
    rest = PrefixedName
    XMLLiteral = PrefixedName


escapers.extend([
    (Node, lambda x: x.subject),
    (RDFTerm, str),
])
