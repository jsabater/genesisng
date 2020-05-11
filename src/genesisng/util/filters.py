# -*- coding: utf-8 -*-
from sqlalchemy import or_, and_


def parse_filters(filters, nexus, cols, query):
    """
    Converts the filters received through query string, which have already been
    parsed by `parse_args`, into conditions for the Query object of SQLAlchemy.

    :param filters: A list of filters, each with field, operator and value.
    :type filters: List of tuples

    :param nexus: The operator to compare the field with the value.
    :type nexus: String

    :param cols: A list of the attributes of the entity as table columns.
    :type cols: :class:`~sqlalchemy:sqlalchemy.sql.base.ImmutableColumnCollection`

    :param query: The SQLAlchemy Query object being constructed.
    :type query: :class:`~sqlalchemy:sqlalchemy.orm.query.Query`

    :returns: A modified Query object that include filters.
    :rtype: :class:`~sqlalchemy:sqlalchemy.orm.query.Query`
    """

    # List of valid operators as lambda funcions
    OPERATORS = {
        'eq': lambda f, v: f == v,
        'ne': lambda f, v: f != v,
        'gt': lambda f, v: f > v,
        'lt': lambda f, v: f < v,
        'gte': lambda f, v: f >= v,
        'lte': lambda f, v: f <= v
    }

    # Process filters
    clauses = []
    for f in filters:
        field, operator, value = f
        clauses.append(OPERATORS[operator](cols[field], value))

    # Tie filters together using the operator
    if nexus == 'or':
        query = query.filter(or_(*clauses))
    else:
        query = query.filter(and_(*clauses))

    # Return the modified query object
    return query
