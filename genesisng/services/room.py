# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service, Integer, Float, List
from genesisng.schema.room import Room
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime


class Get(Service):
    """Service class to get a room by id."""
    """Channel /genesisng/rooms/{id}/get."""

    class SimpleIO:
        input_required = (Integer('id'))
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
                self.response.headers['Location'] = url.format(id=room.id)

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
        input_required = (Integer('id'))

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
        input_required = (Integer('id'))
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

    model = Room
    criteria_allowed = ('id', 'number')
    direction_allowed = ('asc', 'desc')
    filters_allowed = ('id', 'floor_no', 'sgl_beds', 'dbl_beds', 'code')
    comparisons_allowed = ('lt', 'lte', 'eq', 'ne', 'gte', 'gt')
    operators_allowed = ('and', 'or')
    fields_allowed = ('id', 'floor_no', 'room_no', 'name', 'sgl_beds',
                      'dbl_beds', 'supplement', 'code', 'accommodates',
                      'number', 'deleted')
    search_allowed = ()

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('fields'), List('operator'),
                          List('search'))
        output_required = ('count')
        output_optional = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code', 'name', 'accommodates',
                           'number')
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        default_page_size = int(
            self.user_config.genesisng.database.default_page_size)
        max_page_size = int(self.user_config.genesisng.database.max_page_size)
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

            if direction == 'asc':
                query = query.order_by(Cols[criteria].asc())
            else:
                query = query.order_by(Cols[criteria].desc())

            if search:
                clauses = []
                for s in self.search_allowed:
                    clauses.append(Cols[s].ilike(s))

                query = query.filter(or_(*clauses))

            # Calculate limit and offset
            limit = size
            offset = size * (page - 1)
            query = query.offset(offset)
            query = query.limit(limit)

            # Execute query
            result = query.all()

            # Return result
            self.response.payload[:] = result if result else []
