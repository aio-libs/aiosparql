from datetime import date, datetime, time
from decimal import Decimal


__all__ = [
    "escape_any", "escape_string", "escape_datetime", "escape_date",
    "escape_time", "escape_boolean",
]


def escape_any(value):
    """
    Section 4.1.2 defines SPARQL shortened forms
    https://www.w3.org/TR/2013/REC-sparql11-query-20130321/#QSynLiterals

    Examples of literal syntax in SPARQL include:

        "chat"
        'chat'@fr with language tag "fr"
        "xyz"^^<http://example.org/ns/userDatatype>
        "abc"^^appNS:appDataType
        '''The librarian said, "Perhaps you would enjoy 'War and Peace'."'''
        1, which is the same as "1"^^xsd:integer
        1.3, which is the same as "1.3"^^xsd:decimal
        1.300, which is the same as "1.300"^^xsd:decimal
        1.0e6, which is the same as "1.0e6"^^xsd:double
        true, which is the same as "true"^^xsd:boolean
        false, which is the same as "false"^^xsd:boolean
    """
    from .syntax import Node, RDFTerm

    if isinstance(value, type):
        raise TypeError("object %r is not an instance" % value)
    elif isinstance(value, Node):
        return value.subject
    elif isinstance(value, bool):
        return escape_boolean(value)
    elif isinstance(value, datetime):
        return escape_datetime(value)
    elif isinstance(value, date):
        return escape_date(value)
    elif isinstance(value, time):
        return escape_time(value)
    elif isinstance(value, float):
        return escape_float(value)
    elif isinstance(value, (RDFTerm, int, Decimal)):
        return str(value)
    else:
        return escape_string(str(value))


_string_replacements = [
    # always replace first the \ to avoid doubling the future ones
    ('\\', '\\\\'),
    ('"', '\\"'),
    ('\n', "\\n"),
    ('\r', "\\r"),
]


def escape_string(value):
    for old, new in _string_replacements:
        value = value.replace(old, new)
    return '"%s"' % value


def escape_datetime(value):
    return '"%s"^^xsd:dateTime' % value.isoformat()


def escape_date(value):
    return '"%s"^^xsd:date' % value.isoformat()


def escape_time(value):
    return '"%s"^^xsd:time' % value.isoformat()


def escape_boolean(value):
    return "true" if value else "false"


def escape_float(value):
    """
    Python's float are usually double:
    https://docs.python.org/3.6/library/stdtypes.html#numeric-types-int-float-complex
    """
    return '"%s"^^xsd:double' % value
