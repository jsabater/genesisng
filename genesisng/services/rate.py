# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service, Integer, Boolean
from genesisng.schema.rate import Rate
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from urlparse import parse_qs


class Get(Service):
    """Service class to get a rate by id."""
    """Channel /genesisng/rates/get/{id}."""

    class SimpleIO(object):
        input_required = ('id')
        output_optional = ('id', 'date_from', 'date_to', 'base_price',
                           'bed_price', 'published', 'days')

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Rate).\
                filter(and_(Rate.id == id_, Rate.published .is_(True))).\
                one_or_none()

            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class Create(Service):
    """Service class to create a new rate."""
    """Channel /genesisng/rates/create."""

    class SimpleIO:
        input_required = ('date_from', 'date_to', 'base_price', 'bed_price')
        input_optional = (Boolean('published'))
        output_optional = ('id', 'date_from', 'date_to', 'base_price',
                           'bed_price', 'published', 'days')
        skip_empty_keys = True

    def handle(self):
        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        rate = Rate(
            date_from=p.date_from,
            date_to=p.date_to,
            base_price=p.base_price,
            bed_price=p.bed_price)
        rate.published = p.get('published', False)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(rate)
                session.commit()
                self.response.status_code = CREATED
                self.response.payload = rate
                url = self.user_config.genesisng.location.rates
                self.response.headers['Location'] = '%s/%s' % (url, rate.id)

            except IntegrityError:
                # Constraint prevents overlapping dates.
                session.rollback()
                self.response.status_code = CONFLICT
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948
                self.response.payload = ''


class Delete(Service):
    """Service class to delete an existing rate."""
    """Channel /genesisng/rates/delete/{id}"""

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            deleted = session.query(Rate).filter(Rate.id == id_).delete()
            session.commit()

            if deleted:
                self.response.status_code = NO_CONTENT
                self.response.payload = ''
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class Update(Service):
    """Service class to update an existing rate."""
    """Channel /genesisng/rates/update/{id}"""

    class SimpleIO:
        input_required = ('id')
        input_optional = ('date_from', 'date_to', 'base_price', 'bed_price',
                          'published')
        output_optional = ('id', 'date_from', 'date_to', 'base_price',
                           'bed_price', 'published', 'days')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input
        rate = Rate(
            id=id_,
            date_from=p.date_from,
            date_to=p.date_to,
            base_price=p.base_price,
            bed_price=p.bed_price,
            published=p.published)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Rate).filter(Rate.id == id_).one_or_none()

            if result:
                # Update dictionary keys
                result.date_from = rate.date_from
                result.date_to = rate.date_to
                result.base_price = rate.base_price
                result.bed_price = rate.bed_price
                result.published = rate.published
                session.commit()
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class List(Service):
    """Service class to get a list of all rates in the system."""
    """Channel /genesisng/rates/list."""

    class SimpleIO:
        input_optional = ('page', 'size', 'sort_by', 'order_by', 'fields')
        output_optional = ('id', 'date_from', 'date_to', 'base_price',
                           'bed_price', 'published', 'days')
        output_repeated = True
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        default_page_size = int(
            self.user_config.genesisng.database.default_page_size)
        max_page_size = int(self.user_config.genesisng.database.max_page_size)

        # TODO: Have a default order_by and sort_by in the KVDB?
        default_order_by = 'id'
        default_sort_by = 'asc'

        # Pagination is always mandatory
        page = 1
        size = default_page_size

        # Sorting is always mandatory
        order_by = default_order_by
        sort_by = default_sort_by

        # Filtering is optional
        # Format: filters=field|operator|value (multiple)
        filters = []

        # Fields projection and search are not allowed

        # Check for parameters in the query string
        qs = parse_qs(self.wsgi_environ['QUERY_STRING'])
        if qs:

            # Handle pagination
            try:
                page = int(qs['page'][0])
                page = 1 if page < 1 else page

                size = int(qs['size'][0])
                size = default_page_size if size < 1 else size
                size = default_page_size if size > max_page_size else size
            except (ValueError, KeyError, IndexError):
                # Assume default values instead of returning 400 Bad Request
                pass

            # Handle sorting
            try:
                order_by = qs['order_by'][0].lower()
                # Fields allowed for ordering are id, name, surname, gender,
                # email, birthdate and country
                if order_by not in ('id', 'date_from', 'date_to', 'base_price',
                                    'bed_price'):
                    order_by = default_order_by

                sort_by = qs['sort_by'][0].lower()
                sort_by = default_sort_by if sort_by not in (
                    'asc', 'desc') else sort_by
            except (ValueError, KeyError, IndexError):
                # Assume default values instead of returning 400 Bad Request
                pass

            # Handle filtering
            try:
                for f in qs['filters']:
                    field, operator, value = f.split('|')
                    if field not in ('id', 'date_from', 'date_to',
                                     'base_price', 'bed_price'):
                        raise ValueError(
                            'Field %s is not allowed for filtering' % field)
                    if operator not in ('lt', 'lte', 'eq', 'ne', 'gte', 'gt'):
                        raise ValueError(
                            'Operator %s is not allowed for filtering' %
                            operator)
                    filters.append((field, operator, value))
            except (ValueError, KeyError):
                # Do not apply any filtering instead of returning 400 Bad
                # Request
                pass

        # Calculate limit and offset
        limit = size
        offset = size * (page - 1)

        # Calculate criteria and direction
        criteria = order_by
        direction = sort_by

        # Prepare filters
        # TODO: Use sqlalchemy-filters?
        # https://pypi.org/project/sqlalchemy-filters/
        conditions = []
        for f in filters:
            field, operator, value = f
            if operator == 'lt':
                conditions.append(Rate.__table__.columns[field] < value)
            elif operator == 'lte':
                conditions.append(Rate.__table__.columns[field] <= value)
            elif operator == 'eq':
                conditions.append(Rate.__table__.columns[field] == value)
            elif operator == 'ne':
                conditions.append(Rate.__table__.columns[field] != value)
            elif operator == 'gte':
                conditions.append(Rate.__table__.columns[field] >= value)
            elif operator == 'gt':
                conditions.append(Rate.__table__.columns[field] > value)

        # Execute query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))
            for c in conditions:
                query = query.filter(c)
            if direction == 'asc':
                query = query.order_by(Rate.__table__.columns[criteria].asc())
            else:
                query = query.order_by(Rate.__table__.columns[criteria].desc())
            query = query.offset(offset)
            query = query.limit(limit)
            result = query.all()
            self.response.payload[:] = result if result else []