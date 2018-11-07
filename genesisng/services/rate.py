# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service, Integer, Float, Date, Boolean, List
from genesisng.schema.rate import Rate
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError


class Get(Service):
    """Service class to get a rate by id."""
    """Channel /genesisng/rates/{id}/get."""

    class SimpleIO(object):
        input_required = (Integer('id'))
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


class Create(Service):
    """Service class to create a new rate."""
    """Channel /genesisng/rates/create."""

    class SimpleIO:
        input_required = (Date('date_from'), Date('date_to'),
                          Float('base_price'), Float('bed_price'))
        input_optional = (Boolean('published'),)
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
                self.response.headers['Location'] = url.format(id=rate.id)

            except IntegrityError:
                # Constraint prevents overlapping dates.
                session.rollback()
                self.response.status_code = CONFLICT
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class Delete(Service):
    """Service class to delete an existing rate."""
    """Channel /genesisng/rates/{id}/delete"""

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
            else:
                self.response.status_code = NOT_FOUND


class Update(Service):
    """Service class to update an existing rate."""
    """Channel /genesisng/rates/{id}/update"""

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = (Date('date_from'), Date('date_to'),
                          Float('base_price'), Float('bed_price'),
                          Boolean('published', default=False))
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


class List(Service):
    """Service class to get a list of all rates in the system."""
    """Channel /genesisng/rates/list."""

    model = Rate
    criteria_allowed = ('id', 'date_from', 'date_to', 'base_price',
                        'bed_price')
    direction_allowed = ('asc', 'desc')
    filters_allowed = ('id', 'date_from', 'date_to', 'base_price', 'bed_price')
    comparisons_allowed = ('lt', 'lte', 'eq', 'ne', 'gte', 'gt')
    operators_allowed = ('and', 'or')
    fields_allowed = ()
    search_allowed = ()

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('fields'), List('operator'),
                          List('search'))
        # Fields projection is not allowed, so all fields are mandatory
        output_required = ('count')
        output_optional = ('id', 'date_from', 'date_to', 'base_price',
                           'bed_price', 'published', 'days')
        output_repeated = True
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        default_page_size = int(
            self.user_config.genesisng.pagination.default_page_size)
        max_page_size = int(self.user_config.genesisng.pagination.max_page_size)
        Cols = self.model.__table__.columns

        # TODO: Have these default values in user config?
        default_criteria = 'id'
        default_direction = 'asc'
        default_operator = 'and'

        # Page number
        try:
            page = int(self.request.input.page[0])
        except (ValueError, KeyError, IndexError):
            page = 1

        # Page size
        try:
            size = int(self.request.input.size[0])
        except (ValueError, KeyError, IndexError):
            size = default_page_size

        # Order by
        try:
            criteria, direction = self.request.input.sort[0].lower().split('|')
        except (ValueError, KeyError, IndexError, AttributeError):
            criteria = default_criteria
            direction = default_direction

        # Filters
        try:
            filters = self.request.input.filters
            operator = self.request.input.operator[0]
        except (ValueError, KeyError, IndexError):
            filters = []
            operator = default_operator

        # Fields projection
        try:
            fields = self.request.input.fields
        except (ValueError, KeyError):
            fields = []

        # Search
        try:
            search = self.request.input.search[0]
        except (ValueError, KeyError, IndexError):
            search = None

        # Check and adjust parameter values

        # Handle pagination
        page = 1 if page < 1 else page
        size = default_page_size if size < 1 else size
        size = default_page_size if size > max_page_size else size

        # Handle sorting
        if criteria not in self.criteria_allowed:
            criteria = default_criteria
        if direction not in self.direction_allowed:
            direction = default_direction

        # Handle filtering
        conditions = []
        for filter_ in filters:
            field, comparison, value = filter_.split('|')
            if field in self.filters_allowed and comparison in self.comparisons_allowed:
                    conditions.append((field, comparison, value))
        if operator not in self.operators_allowed:
            operator = default_operator

        # Handle fields projection
        columns = []
        for f in fields:
            if f in self.fields_allowed:
                columns.append(f)

        # Handle search
        if not self.search_allowed:
            search = None

        # Compose query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))

            # Add columns
            if not columns:
                columns = self.fields_allowed

            for c in columns:
                query = query.add_columns(Cols[c])

            # Prepare filters
            # TODO: Use sqlalchemy-filters?
            # https://pypi.org/project/sqlalchemy-filters/
            # TODO: Use a map instead of if..else?
            # m = {'lt': '<', 'lte': '<=', 'eq': '==', 'ne': '!=', 'gte': '>=', 'gt': '>'}
            if conditions:
                clauses = []
                for c in conditions:
                    f, o, v = c
                    if o == 'lt':
                        clauses.append(Cols[f] < v)
                    elif o == 'lte':
                        clauses.append(Cols[f] <= v)
                    elif o == 'eq':
                        clauses.append(Cols[f] == v)
                    elif o == 'ne':
                        clauses.append(Cols[f] != v)
                    elif o == 'gte':
                        clauses.append(Cols[f] >= v)
                    elif o == 'gt':
                        clauses.append(Cols[f] > v)
                if operator == 'or':
                    query = query.filter(or_(*clauses))
                else:
                    query = query.filter(and_(*clauses))

            # Search
            if search:
                clauses = []
                for s in self.search_allowed:
                    clauses.append(Cols[s].ilike(search))
                query = query.filter(or_(*clauses))

            # Order by
            if direction == 'asc':
                query = query.order_by(Cols[criteria].asc())
            else:
                query = query.order_by(Cols[criteria].desc())

            # Calculate limit and offset
            limit = size
            offset = size * (page - 1)
            query = query.offset(offset)
            query = query.limit(limit)

            # Execute query
            result = query.all()

            # Return result
            if result:
                self.response.payload[:] = result
                self.response.status_code = OK
            else:
                self.response.status_code = NO_CONTENT
