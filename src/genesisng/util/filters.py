# -*- coding: utf-8 -*-
from sqlalchemy import or_, and_


def parse_filters(filters, operator, cols, query):
    """
    Converts filters received through query string, which have already been
    parsed by `parse_args`, into conditions for the Query object of SQLAlchemy.

    :param filters: A list of filters, each with field, operator and value.
    :type filters: List of tuples

    :param operator: The operator to compare the field with the value.
    :type operator: String

    :param cols: A list of the attributes of the entity as table columns.
    :type cols: sqlalchemy.sql.base.ImmutableColumnCollection

    :param query: The SQLAlchemy Query object being constructed.
    :type query: sqlalchemy.orm.query.Query

    :returns: A modified Query object that include filters.
    :rtype: sqlalchemy.orm.query.Query
    """

    OPERATORS = {
        'eq': lambda f, a: f == a,
        'ne': lambda f, a: f != a,
        'gt': lambda f, a: f > a,
        'lt': lambda f, a: f < a,
        'gte': lambda f, a: f >= a,
        'lte': lambda f, a: f <= a
    }

    # Process filters
    clauses = []
    for f in filters:
        field, operator, value = f
        # TODO: Turn the follwing if..else block into one sentence
        # clauses.append(cols[field] OPERATORS[operator] value)
        if operator == 'lt':
            clauses.append(cols[field] < value)
        elif operator == 'lte':
            clauses.append(cols[field] <= value)
        elif operator == 'eq':
            clauses.append(cols[field] == value)
        elif operator == 'ne':
            clauses.append(cols[field] != value)
        elif operator == 'gte':
            clauses.append(cols[field] >= value)
        elif operator == 'gt':
            clauses.append(cols[field] > value)

    # Tie filters together using the operator
    if operator == 'or':
        query = query.filter(or_(*clauses))
    else:
        query = query.filter(and_(*clauses))

    # Return the modified query object
    return query
