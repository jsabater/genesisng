# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service, Integer, Float
from genesisng.schema.room import Room
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from urlparse import parse_qs
from datetime import datetime


class Get(Service):
    """Service class to get a room by id."""
    """Channel /genesisng/rooms/{id}/get."""

    class SimpleIO:
        input_required = (Integer('id'),)
        output_required = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code')
        output_optional = ('name', 'accommodates', 'number')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Room).\
                filter(and_(Room.id == id_, Room.deleted.is_(None))).\
                one_or_none()

            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class Create(Service):
    """Service class to create a new room."""
    """Channel /genesisng/rooms/create."""

    class SimpleIO:
        input_required = (Integer('floor_no'), Integer('room_no'),
                          Integer('sgl_beds'), Integer('dbl_beds'),
                          Float('supplement'))
        input_optional = ('name')
        output_required = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code')
        output_optional = ('name', 'accommodates', 'number')
        skip_empty_keys = True

    def handle(self):
        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection
        p = self.request.input
        room = Room(floor_no=p.floor_no, room_no=p.room_no,
                    sgl_beds=p.sgl_beds, dbl_beds=p.dbl_beds,
                    supplement=p.supplement, code=p.code)
        room.name = p.get('name', None)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(room)
                session.commit()
                self.response.status_code = CREATED
                self.response.payload = room
                url = self.user_config.genesisng.location.rooms
                self.response.headers['Location'] = url.format(id, room.id)

            except IntegrityError:
                # Constraint prevents duplication of codes or room numbers.
                session.rollback()
                self.response.status_code = CONFLICT
                # TODO: Return well-formed error response?
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948
                self.response.payload = ''


class Delete(Service):
    """Service class to delete an existing room."""
    """Channel /genesisng/rooms/{id}/delete"""

    class SimpleIO:
        input_required = (Integer('id'),)

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Room).\
                filter(and_(Room.id == id_, Room.deleted.is_(None))).\
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


class Update(Service):
    """Service class to update an existing room."""
    """Channel /genesisng/rooms/{id}/update"""

    class SimpleIO:
        input_required = (Integer('id'),)
        input_optional = (Integer('floor_no'), Integer('room_no'), 'name',
                          Integer('sgl_beds'), Integer('dbl_beds'),
                          Float('supplement'), 'code')
        output_required = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code')
        output_optional = ('name', 'accommodates', 'number')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input
        room = Room(floor_no=p.floor_no, room_no=p.room_no, name=p.name,
                    sgl_beds=p.sgl_beds, dbl_beds=p.dbl_beds,
                    supplement=p.supplement, code=p.code)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Room).\
                filter(and_(Room.id == id_, Room.deleted.is_(None))).\
                one_or_none()

            if result:
                # Update dictionary keys
                result.floor_no = room.floor_no
                result.room_no = room.room_no
                result.name = room.name
                result.sgl_beds = room.sgl_beds
                result.dbl_beds = room.dbl_beds
                result.supplement = room.supplement
                result.code = room.code
                session.commit()
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class List(Service):
    """Service class to get a list of all rooms in the system."""
    """Channel /genesisng/rooms/list."""

    class SimpleIO:
        input_optional = (Integer('page'), Integer('size'), 'sort_by',
                          'order_by', 'filters', 'search', 'fields')
        output_required = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code')
        output_optional = ('name', 'accommodates', 'number')
        skip_empty_keys = True
        output_repeated = True

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

        # Fields projection is optional
        # Format: fields=field (multiple)
        fields = []

        # Search is not allowed
        # search = None

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
                # Fields allowed for ordering are id and number
                if order_by not in ('id', 'number'):
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
                    if field not in ('id', 'floor_no', 'sgl_beds', 'dbl_beds',
                                     'code'):
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

            # Handle fields projection
            try:
                for field in qs['fields']:
                    if field not in ('id', 'floor_no', 'room_no', 'name',
                                     'sgl_beds', 'dbl_beds', 'supplement',
                                     'code', 'accommodates', 'number',
                                     'deleted'):
                        raise ValueError(
                            'Field %s is not allowed for projection' % field)
                    fields.append(field)
            except (ValueError, KeyError):
                # Do not apply any fields projection instead of returning 400
                # Bad Request
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
                conditions.append(Room.__table__.columns[field] < value)
            elif operator == 'lte':
                conditions.append(Room.__table__.columns[field] <= value)
            elif operator == 'eq':
                conditions.append(Room.__table__.columns[field] == value)
            elif operator == 'ne':
                conditions.append(Room.__table__.columns[field] != value)
            elif operator == 'gte':
                conditions.append(Room.__table__.columns[field] >= value)
            elif operator == 'gt':
                conditions.append(Room.__table__.columns[field] > value)

        # Prepare fields projection
        columns = []
        if not fields:
            fields = ('id', 'floor_no', 'room_no', 'name', 'sgl_beds',
                      'dbl_beds', 'supplement', 'code', 'accommodates',
                      'number', 'deleted')
        columns = [Room.__table__.columns[f] for f in fields]

        # Execute query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))
            for c in columns:
                query = query.add_columns(c)
            for c in conditions:
                query = query.filter(c)
            if direction == 'asc':
                query = query.order_by(Room.__table__.columns[criteria].asc())
            else:
                query = query.order_by(
                    Room.__table__.columns[criteria].desc())
            query = query.offset(offset)
            query = query.limit(limit)
            result = query.all()
            self.response.payload[:] = result if result else []
