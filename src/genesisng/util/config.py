# -*- coding: utf-8 -*-
from bunch import Bunch


def parse_args(input, allowed, pagination):
    """
    Parses arguments received through query string, checking and adjusting
    their values.

    :param input: The input fields to be processed.
    :type input: Bunch dict

    :param allowed: The fields in which sorting, filtering, projection and
        search is allowed for this entity when listing items. Each key in the
        dictionary contains a tuple of fields.
    :type allowed: Bunch dict

    :param pagination: The items in the pagination section from the config.ini
        file, which includes a number of variables that are common to all
        listings in all services
    :type pagination: Bunch dict

    :returns: A dictionary with final values for each key used when composing
        the query through SQLAlchemy.
    :rtype: Bunch dict
    """

    # Page number can only be a positive integer greater than 0
    try:
        page = int(input.page[0])
    except (ValueError, KeyError, IndexError):
        page = int(pagination.first_page)
    page = 1 if page < 1 else page

    # Page size must be greater than zero and less or equal than the maximum
    # page size defined in the configuration
    default_page_size = int(pagination.default_page_size)
    try:
        size = int(input.size[0])
    except (ValueError, KeyError, IndexError):
        size = default_page_size
    if size < 1:
        size = default_page_size
    if size > int(pagination.max_page_size):
        size = default_page_size

    # Order by is made of a criteria field and a direction.
    # Criteria can only be one of the allowed fields.
    # Direction can only be 'asc' or 'desc', as per the config.ini file
    try:
        criteria, direction = input.sort[0].lower().split('|')
        if criteria not in allowed.criteria:
            criteria = pagination.default_criteria
        if direction not in pagination.direction_allowed:
            direction = pagination.default_direction
    except (ValueError, KeyError, IndexError, AttributeError):
        criteria = pagination.default_criteria
        direction = pagination.default_direction

    # Filters allow filtering by field and value through an operator. Multiple
    # filters are allowed, called conditions.
    # Operators can only be 'and' or 'or', as per the config.ini file
    # You can only filter by a field that has been allowed for this entity.
    try:
        filters = input.filters
        operator = input.operator[0]
    except (ValueError, KeyError, IndexError):
        filters = []
        operator = pagination.default_operator
    conditions = []
    for filter_ in filters:
        # Field, comparison, value
        f, c, v = filter_.split('|')
        if f in allowed.filters and \
           c in pagination.comparisons_allowed:
            conditions.append((f, c, v))
    if operator not in pagination.operators_allowed:
        operator = pagination.default_operator

    # Fields projection allows returned a sub-set of each record.
    # Requested fields are checked against the list of available fields and
    # returned as columns.
    try:
        fields = input.fields
    except (ValueError, KeyError):
        fields = []
    columns = []
    for f in fields:
        if f in allowed.fields:
            columns.append(f)

    # Search allows a term to be used to filter returned records in a
    # case-insensitive manner (ilike). Only check made here is whether search
    # is allowed for this entity or not.
    try:
        term = input.search[0].lower()
    except (ValueError, KeyError, IndexError):
        term = None
    if not allowed.search:
        term = None

    return Bunch({
        'page': page,
        'size': size,
        'criteria': criteria,
        'direction': direction,
        'conditions': conditions,
        'operator': operator,
        'columns': columns,
        'search': term
    })
