# -*- coding: utf-8 -*-
from bunch import Bunch


def parse_args(input, allowed, pagination, logger):
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
        logger.info("Discarting size: %s" % size)
        size = default_page_size

    # Calculate limit and offset from page and size
    limit = size
    offset = size * (page - 1)

    # Order by is made of a criteria field and a direction.
    # Criteria can only be one of the allowed fields.
    # Direction can only be 'asc' or 'desc', as per the config.ini file
    try:
        criteria, direction = input.sort[0].lower().split('|')
        if criteria not in allowed.criteria:
            logger.info("Discarting criteria: %s" % criteria)
            criteria = pagination.default_criteria
        if direction not in pagination.direction_allowed:
            logger.info("Discarting direction: %s" % direction)
            direction = pagination.default_direction
    except (ValueError, KeyError, IndexError, AttributeError):
        criteria = pagination.default_criteria
        direction = pagination.default_direction

    # Filters allow filtering by field and value through an operator. Multiple
    # filters are allowed, called conditions.
    # You can only filter by a field that has been allowed for this entity.
    try:
        filters = input.filters
    except (ValueError, KeyError, IndexError):
        filters = []
    conditions = []
    for f in filters:
        try:
            field, comparison, value = f.split('|')
            if field in allowed.filters:
                if comparison in pagination.comparisons_allowed:
                    conditions.append((field, comparison, value))
                else:
                    logger.info("Discarting filter: %s" % f)
            else:
                logger.info("Discarting filter: %s" % f)
        except ValueError:
            logger.info("Invalid filter argument: %s" % f)

    # Operator instructs how to join filters in the WHERE clause.
    # Operator can only be 'and' or 'or', as per the config.ini file
    try:
        operator = input.operator[0]
    except (ValueError, KeyError, IndexError):
        operator = pagination.default_operator
    if operator not in pagination.operators_allowed:
        logger.info("Discarting operator: %s" % operator)
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
        else:
            logger.info("Discarting projection field: %s" % f)

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
        'limit': limit,
        'offset': offset,
        'criteria': criteria,
        'direction': direction,
        'filters': conditions,
        'operator': operator,
        'columns': columns,
        'search': term
    })
