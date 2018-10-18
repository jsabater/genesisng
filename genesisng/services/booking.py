# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service
from zato.server.service import Integer, Float, Date, DateTime, Dict, List
from genesisng.schema.booking import Booking
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime


class Get(Service):
    """Service class to get a booking by id."""
    """Channel /genesisng/bookings/{id}/get."""

    class SimpleIO(object):
        input_required = (Integer('id'))
        output_required = ('id', 'id_guest', 'id_room',
                           DateTime('reserved'), 'guests', Date('check_in'),
                           Date('check_out'), 'base_price', 'taxes_percentage',
                           'taxes_value', 'total_price', 'locator',
                           'pin', 'status', 'meal_plan',
                           Dict('additional_services'), 'uuid')
        output_optional = (DateTime('checked_in'), DateTime('checked_out'),
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
                self.response.payload = ''


class Locate(Service):
    """Service class to get a booking by locator."""
    """Channel /genesisng/bookings/{locator}/locate."""

    class SimpleIO(object):
        input_required = (Integer('id'))
        output_required = ('id', 'id_guest', 'id_room',
                           DateTime('reserved'), 'guests', Date('check_in'),
                           Date('check_out'), 'base_price', 'taxes_percentage',
                           'taxes_value', 'total_price', 'locator',
                           'pin', 'status', 'meal_plan',
                           Dict('additional_services'), 'uuid')
        output_optional = (DateTime('checked_in'), DateTime('checked_out'),
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
                self.response.payload = ''


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
                self.response.payload = ''
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


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
        output_required = ('id', 'id_guest', 'id_room',
                           DateTime('reserved'), 'guests', Date('check_in'),
                           Date('check_out'), 'base_price', 'taxes_percentage',
                           'taxes_value', 'total_price', 'locator',
                           'pin', 'status', 'meal_plan',
                           Dict('additional_services'), 'uuid')
        output_optional = (DateTime('checked_in'), DateTime('checked_out'),
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
                self.response.payload = ''


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
                self.response.payload = ''
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


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
        output_required = ('id', 'id_guest', 'id_room',
                           DateTime('reserved'), 'guests', Date('check_in'),
                           Date('check_out'), 'base_price', 'taxes_percentage',
                           'taxes_value', 'total_price', 'locator',
                           'pin', 'status', 'meal_plan',
                           Dict('additional_services'), 'uuid')
        output_optional = (DateTime('checked_in'), DateTime('checked_out'),
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
                self.response.payload = ''


class List(Service):
    """Service class to get a list of all bookings in the system."""
    """Channel /genesisng/bookings/list."""
    """Search is not allowed."""

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort_by'),
                          List('order_by'), List('filters'), List('fields'))
        output_required = ('count')
        output_optional = ('id', 'id_guest', 'id_room',
                           DateTime('reserved'), 'guests', Date('check_in'),
                           Date('check_out'), 'base_price', 'taxes_percentage',
                           'taxes_value', 'total_price', 'locator',
                           'pin', 'status', 'meal_plan',
                           Dict('additional_services'), 'uuid',
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'))
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        default_page_size = int(
            self.user_config.genesisng.database.default_page_size)
        max_page_size = int(self.user_config.genesisng.database.max_page_size)

        # TODO: Have a default order_by and sort_by in the user config?
        default_order_by = 'id'
        default_sort_by = 'asc'

        # Pagination is always enforced.
        # Format: page and (page) size.
        # Sorting is always enforced.
        # Format: order_by (direction) and sort_by (criteria)
        # Filtering is optional. Multiple filters are allowed.
        # Format: filters=field|operator|value
        # Fields projection is optional. Multiple fields are allowed.
        # Format: fields=field
        # Search is not allowed.

        # In case of error, do not return 400 Bad Request but, instead, assume
        # default parameter values.

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
            order_by = self.request.input.order_by[0].lower()
        except (ValueError, KeyError, IndexError):
            order_by = default_order_by

        # Sort order
        try:
            sort_by = self.request.input.sort_by[0].lower()
        except (ValueError, KeyError, IndexError):
            sort_by = default_sort_by

        # Filters
        try:
            filters = self.request.input.filters
        except (ValueError, KeyError):
            filters = []

        # Fields projection
        try:
            fields = self.request.input.fields
        except (ValueError, KeyError):
            fields = []

        # Check and adjust parameter values

        # Handle pagination
        page = 1 if page < 1 else page
        size = default_page_size if size < 1 else size
        size = default_page_size if size > max_page_size else size

        # Handle sorting
        order_by_allowed = ('id', 'id_guest', 'id_room', 'check_in',
                            'check_out')
        sort_by_allowed = ('asc', 'desc')
        if order_by not in order_by_allowed:
            order_by = default_order_by
        if sort_by not in sort_by_allowed:
            sort_by = default_sort_by

        # Handle filtering
        filters_allowed = ('id', 'id_guest', 'id_room', 'reserved', 'guests',
                           'check_in', 'check_out', 'base_price',
                           'total_price', 'status', 'meal_plan',
                           'additional_services')
        operators_allowed = ('lt', 'lte', 'eq', 'ne', 'gte', 'gt')
        conditions = []
        for f in filters:
            field, operator, value = f.split('|')
            if field in filters_allowed and operator in operators_allowed:
                conditions.append((field, operator, value))

        # Handle fields projection
        allowed_fields = ('id', 'id_guest', 'id_room', 'reserved', 'guests',
                          'check_in', 'check_out', 'checked_in', 'checked_out',
                          'cancelled', 'base_price', 'taxes_percentage',
                          'taxes_value', 'total_price', 'locator', 'pin',
                          'status', 'meal_plan', 'additional_services', 'uuid',
                          'deleted')
        columns = []
        for f in fields:
            if f in allowed_fields:
                columns.append(f)

        # Compose query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))

            # Add columns
            if not columns:
                columns = allowed_fields

            for c in columns:
                query = query.add_columns(Booking.__table__.columns[c])

            # Prepare filters
            # TODO: Use sqlalchemy-filters?
            # https://pypi.org/project/sqlalchemy-filters/
            for c in conditions:
                field, operator, value = c
                if operator == 'lt':
                    query = query.filter(
                        Booking.__table__.columns[field] < value)
                elif operator == 'lte':
                    query = query.filter(
                        Booking.__table__.columns[field] <= value)
                elif operator == 'eq':
                    query = query.filter(
                        Booking.__table__.columns[field] == value)
                elif operator == 'ne':
                    query = query.filter(
                        Booking.__table__.columns[field] != value)
                elif operator == 'gte':
                    query = query.filter(
                        Booking.__table__.columns[field] >= value)
                elif operator == 'gt':
                    query = query.filter(
                        Booking.__table__.columns[field] > value)

            if sort_by == 'asc':
                query = query.order_by(
                    Booking.__table__.columns[order_by].asc())
            else:
                query = query.order_by(
                    Booking.__table__.columns[order_by].desc())

            # Calculate limit and offset
            limit = size
            offset = size * (page - 1)
            query = query.offset(offset)
            query = query.limit(limit)

            # Execute query
            result = query.all()

            # Return result
            self.response.payload[:] = result if result else []


class Restore(Service):
    """Service class to restore a deleted an existing booking."""
    """Channel /genesisng/bookingss/{id}/restore"""

    class SimpleIO:
        input_required = (Integer('id'))
        output_required = ('id', 'id_guest', 'id_room',
                           DateTime('reserved'), 'guests', Date('check_in'),
                           Date('check_out'), 'base_price', 'taxes_percentage',
                           'taxes_value', 'total_price', 'locator',
                           'pin', 'status', 'meal_plan',
                           Dict('additional_services'), 'uuid')
        output_optional = (DateTime('checked_in'), DateTime('checked_out'),
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
                self.response.payload = ''
