# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service
from zato.server.service import Integer, Float, Date, DateTime, Dict, List
from genesisng.schema.booking import Booking
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime


class Get(Service):
    """Service class to get a booking by id."""
    """Channel /genesisng/bookings/{id}/get."""

    class SimpleIO(object):
        input_required = (Integer('id'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           'base_price', 'taxes_percentage', 'taxes_value',
                           'total_price', 'locator', 'pin', 'status',
                           'meal_plan', Dict('additional_services'), 'uuid',
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'))
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_, Booking.deleted.is_(None))).\
                one_or_none()

            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND


class Locate(Service):
    """Service class to get a booking by locator."""
    """Channel /genesisng/bookings/{locator}/locate."""

    class SimpleIO(object):
        input_required = (Integer('id'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           'base_price', 'taxes_percentage', 'taxes_value',
                           'total_price', 'locator', 'pin', 'status',
                           'meal_plan', Dict('additional_services'), 'uuid',
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'))
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        locator = self.request.input.locator

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.locator == locator,
                            Booking.deleted.is_(None))).\
                one_or_none()

            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND


class Delete(Service):
    """Service class to delete an existing booking."""
    """Channel /genesisng/bookings/{id}/delete"""

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_, Booking.deleted.is_(None))).\
                one_or_none()
            if result:
                # Set deleted field
                result.deleted = datetime.utcnow()
                session.commit()
                self.response.status_code = NO_CONTENT
            else:
                self.response.status_code = NOT_FOUND


class Create(Service):
    """Service class to create a new booking."""
    """Channel /genesisng/bookings/create."""

    class SimpleIO:
        input_required = (Integer('id_guest'), Integer('id_room'),
                          Integer('guests'), Date('check_in'),
                          Date('check_out'), Float('base_price'),
                          Float('taxes_percentage'), Float('taxes_value'),
                          Float('total_price'), 'locator', 'pin')
        input_optional = (DateTime('checked_in'), DateTime('checked_out'),
                          DateTime('cancelled'), 'status', 'meal_plan',
                          Dict('additional_services'), 'uuid')
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           'base_price', 'taxes_percentage', 'taxes_value',
                           'total_price', 'locator', 'pin', 'status',
                           'meal_plan', Dict('additional_services'), 'uuid',
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'))
        skip_empty_keys = True

    def handle(self):
        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        booking = Booking(
            id_guest=p.id_guest,
            id_room=p.id_room,
            guests=p.guests,
            check_in=p.check_in,
            check_out=p.check_out,
            base_price=p.base_price,
            taxes_percentage=p.taxes_percentage,
            taxes_value=p.taxes_value,
            total_price=p.total_price,
            locator=p.locator,
            pin=p.pin,
            status=p.status,
            meal_plan=p.meal_plan,
            additional_services=p.additional_services)
        booking.checked_in = p.get('checked_in', None)
        booking.checked_out = p.get('checked_out', None)
        booking.cancelled = p.get('cancelled', None)
        booking.uuid = p.get('uuid', None)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(booking)
                session.commit()
                self.response.status_code = CREATED
                self.response.payload = booking
                url = self.user_config.genesisng.location.bookings
                self.response.headers['Location'] = url.format(id=booking.id)

            except IntegrityError:
                # Constraint prevents duplication of username or emails.
                session.rollback()
                self.response.status_code = CONFLICT
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class Cancel(Service):
    """Service class to cancel an existing booking."""
    """Channel /genesisng/bookings/{id}/cancel"""

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_,
                            Booking.deleted.is_(None),
                            Booking.cancelled.is_(None))).\
                one_or_none()
            if result:
                # Set cancelled field
                result.cancelled = datetime.utcnow()
                session.commit()
                self.response.status_code = NO_CONTENT
            else:
                self.response.status_code = NOT_FOUND


class Update(Service):
    """Service class to update an existing booking."""
    """Channel /genesisng/bookings/{id}/update"""

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = (Integer('id_guest'), Integer('id_room'),
                          DateTime('reserved'), Integer('guests'),
                          Date('check_in'), Date('check_out'),
                          DateTime('checked_in'), DateTime('checked_out'),
                          DateTime('cancelled'), Float('base_price'),
                          Float('taxes_percentage'), Float('taxes_value'),
                          Float('total_price'), 'locator', 'pin', 'status',
                          'meal_plan', Dict('additional_services'), 'uuid')
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           'base_price', 'taxes_percentage', 'taxes_value',
                           'total_price', 'locator', 'pin', 'status',
                           'meal_plan', Dict('additional_services'), 'uuid',
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'))
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input
        booking = Booking(
            id=id_,
            id_guest=p.id_guest,
            id_room=p.id_room,
            reserved=p.reserved,
            guests=p.guests,
            check_in=p.check_in,
            check_out=p.check_out,
            checked_in=p.checked_in,
            checked_out=p.checked_out,
            base_price=p.base_price,
            taxes_percentage=p.taxes_percentage,
            taxes_value=p.taxes_value,
            total_price=p.total_price,
            locator=p.locator,
            pin=p.pin,
            status=p.status,
            meal_plan=p.meal_plan,
            additional_services=p.additional_services)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(Booking.id == id_).one_or_none()

            if result:
                # Update dictionary keys
                result.id_guest = booking.id_guest
                result.id_room = booking.id_room
                result.reserved = booking.reserved
                result.guests = booking.guests
                result.check_in = booking.check_in
                result.check_out = booking.check_out
                result.checked_in = booking.checked_in
                result.checked_out = booking.checked_out
                result.base_price = booking.base_price
                result.taxes_percentage = booking.taxes_percentage
                result.taxes_value = booking.taxes_value
                result.total_price = booking.total_price
                result.locator = booking.locator
                result.pin = booking.pin
                result.status = booking.status
                result.meal_plan = booking.meal_plan
                result.additional_services = booking.additional_services
                session.commit()
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND


class List(Service):
    """Service class to get a list of all bookings in the system."""
    """Channel /genesisng/bookings/list."""
    """
    Query string parameters:
    * page: the page number (default 1).
    * size: the number of items per page (default in user config).
    * sort: <criteria>|<direction> (default id|asc).
      Direction can be 'asc' or 'desc'.
    * filters: <field>|<comparator>|<value>
      Supported comparators are:
        * lt: less than.
        * lte: less than or equal.
        * eq: equal.
        * ne: not equal.
        * gte: greater than or equal.
        * gt: greater than.
    * operator: applies to all filters (default 'and').
      Supported operators are 'and' and 'or'.
    * fields: <field>.
    Pagination and sorting are always enforced.
    Filtering is optional. Multiple filters allowed. Only one operator.
    Fields projection is optional. Multiple fields allowed.
    Search is not allowed.

    In case of error, it does not return 400 Bad Request but, instead,
    it assumes default parameter values and carries on.
    """

    model = Booking
    criteria_allowed = ('id', 'id_guest', 'id_room', 'check_in', 'check_out')
    direction_allowed = ('asc', 'desc')
    filters_allowed = ('id', 'id_guest', 'id_room', 'reserved', 'guests',
                       'check_in', 'check_out', 'base_price', 'total_price',
                       'status', 'meal_plan', 'additional_services')
    comparisons_allowed = ('lt', 'lte', 'eq', 'ne', 'gte', 'gt')
    operators_allowed = ('and', 'or')
    fields_allowed = ('id', 'id_guest', 'id_room', 'reserved', 'guests',
                      'check_in', 'check_out', 'checked_in', 'checked_out',
                      'cancelled', 'base_price', 'taxes_percentage',
                      'taxes_value', 'total_price', 'locator', 'pin',
                      'status', 'meal_plan', 'additional_services', 'uuid',
                      'deleted')
    search_allowed = ()

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('fields'), List('operator'),
                          List('search'))
        # Fields projection makes all output fields optional
        output_required = ('count')
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           'base_price', 'taxes_percentage', 'taxes_value',
                           'total_price', 'locator', 'pin', 'status',
                           'meal_plan', Dict('additional_services'), 'uuid',
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'))
        skip_empty_keys = True
        output_repeated = True

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
            if field in self.filters_allowed and \
               comparison in self.comparisons_allowed:
                conditions.append((field, comparison, value))
        if operator not in (self.operators_allowed):
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


class Restore(Service):
    """Service class to restore a deleted an existing booking."""
    """Channel /genesisng/bookingss/{id}/restore"""

    class SimpleIO:
        input_required = (Integer('id'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           'base_price', 'taxes_percentage', 'taxes_value',
                           'total_price', 'locator', 'pin', 'status',
                           'meal_plan', Dict('additional_services'), 'uuid',
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'))
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_, Booking.deleted.isnot(None))).\
                one_or_none()

            if result:
                # Update dictionary key
                result.deleted = None
                session.commit()
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
