# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service
from zato.server.service import Integer, Date, DateTime, ListOfDicts, List
from genesisng.schema.guest import Guest
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from urlparse import parse_qs
from datetime import datetime


class Get(Service):
    """Service class to get a guest by id."""
    """Channel /genesisng/guests/{id}/get."""

    class SimpleIO(object):
        input_required = (Integer('id'))
        output_required = ('id', 'name', 'surname', 'gender', 'email')
        output_optional = ('passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Guest).\
                filter(and_(Guest.id == id_, Guest.deleted.is_(None))).\
                one_or_none()

            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class Create(Service):
    """Service class to create a new guest."""
    """Channel /genesisng/guests/create."""

    class SimpleIO:
        input_required = ('name', 'surname', 'gender', 'email')
        input_optional = ('passport', 'address1', 'locality', 'postcode',
                          'province', 'country')
        output_required = ('id', 'name', 'surname', 'gender', 'email')
        output_optional = ('passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone')
        skip_empty_keys = True

    def handle(self):
        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        guest = Guest(
            name=p.name,
            surname=p.surname,
            gender=p.gender,
            email=p.email,
            passport=p.passport,
            address1=p.address1,
            locality=p.locality,
            postcode=p.postcode,
            province=p.province,
            country=p.country)
        guest.address2 = p.get('address2', None)
        guest.birthdate = p.get('birthdate', None)
        guest.home_phone = p.get('home_phone', None)
        guest.mobile_phone = p.get('mobile_phone', None)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(guest)
                session.commit()
                self.response.status_code = CREATED
                self.response.payload = guest
                url = self.user_config.genesisng.location.guests
                self.response.headers['Location'] = url.format(id=guest.id)

            except IntegrityError:
                # Constraint prevents duplication of username or emails.
                session.rollback()
                self.response.status_code = CONFLICT
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948
                self.response.payload = ''


class Delete(Service):
    """Service class to delete an existing guest."""
    """Channel /genesisng/guests/{id}/delete"""

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Guest).\
                filter(and_(Guest.id == id_, Guest.deleted.is_(None))).\
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
    """Service class to update an existing guest."""
    """Channel /genesisng/guests/{id}/update"""

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = ('name', 'surname', 'gender', 'email', 'passport',
                          Date('birthdate'), 'address1', 'address2',
                          'locality', 'postcode', 'province', 'country',
                          'home_phone', 'mobile_phone')
        output_required = ('id', 'name', 'surname', 'gender', 'email')
        output_optional = ('passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input

        # TODO: Clean up self.request.input from empty keys

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                result = session.query(Guest).\
                    filter(and_(Guest.id == id_, Guest.deleted.is_(None))).\
                    one_or_none()

                if result:
                    # TODO: Add request params to skip_empty_keys as per:
                    # https://forum.zato.io/t/leave-the-simpleio-input-optional-out-of-the-input/593/22
                    # result.fromdict(self.request.input, allow_pk=True)

                    # Update dictionary keys
                    if p.name:
                        result.name = p.name
                    if p.surname:
                        result.surname = p.surname
                    if p.gender:
                        result.gender = p.gender
                    if p.email:
                        result.email = p.email
                    if p.passport:
                        result.passport = p.passport
                    if p.birthdate:
                        result.birthdate = p.birthdate
                    if p.address1:
                        result.address1 = p.address1
                    if p.address2:
                        result.address2 = p.address2
                    if p.locality:
                        result.locality = p.locality
                    if p.province:
                        result.province = p.province
                    if p.country:
                        result.country = p.country
                    if p.home_phone:
                        result.home_phone = p.home_phone
                    if p.mobile_phone:
                        result.mobile_phone = p.mobile_phone
                    session.commit()
                    self.response.status_code = OK
                    self.response.payload = result
                else:
                    self.response.status_code = NOT_FOUND
                    self.response.payload = ''
            except IntegrityError:
                # Constraint prevents duplication of emails.
                session.rollback()
                self.response.status_code = CONFLICT
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948
                self.response.payload = ''


class List(Service):
    """Service class to get a list of all guests in the system."""
    """Channel /genesisng/guests/list."""
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
    Search is optional. Passed term is case insensitive.

    In case of error, it does not return 400 Bad Request but, instead,
    it assumes default parameter values and carries on.
    """

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('fields'), List('operator'),
                          List('search'))
        output_required = ('count')
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone',
                           DateTime('deleted'))
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        default_page_size = int(
            self.user_config.genesisng.database.default_page_size)
        max_page_size = int(self.user_config.genesisng.database.max_page_size)

        # TODO: Have a default order_by and sort_by in the KVDB?
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
        criteria_allowed = ('id', 'name', 'surname', 'gender', 'email',
                            'birthdate', 'country')
        direction_allowed = ('asc', 'desc')
        if criteria not in criteria_allowed:
            criteria = default_criteria
        if direction not in direction_allowed:
            direction = default_direction

        # Handle filtering
        filters_allowed = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', 'birthdate', 'address1', 'address2',
                           'locality', 'postcode', 'province', 'country',
                           'home_phone', 'mobile_phone')
        comparisons_allowed = ('lt', 'lte', 'eq', 'ne', 'gte', 'gt')
        operators_allowed = ('and', 'or')
        conditions = []
        for filter_ in filters:
            field, comparison, value = filter_.split('|')
            if field in filters_allowed and comparison in comparisons_allowed:
                conditions.append((field, comparison, value))
        if operator not in (operators_allowed):
            operator = default_operator

        # Handle fields projection
        allowed_fields = ('id', 'name', 'surname', 'gender', 'email',
                          'passport', 'birthdate', 'address1', 'address2',
                          'locality', 'postcode', 'province', 'country',
                          'home_phone', 'mobile_phone', 'deleted')

        columns = []
        for f in fields:
            if f in allowed_fields:
                columns.append(f)

        # Handle search
        search_allowed = ('id', 'name', 'surname', 'gender', 'email',
                          'passport', 'birthdate', 'address1', 'address2',
                          'locality', 'postcode', 'province', 'country',
                          'home_phone', 'mobile_phone', 'deleted')
        if search not in search_allowed:
            search = None

        # Compose query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))

            # Add columns
            if not columns:
                columns = allowed_fields

            for c in columns:
                query = query.add_columns(Guest.__table__.columns[c])

            # Prepare filters
            # TODO: Use sqlalchemy-filters?
            # https://pypi.org/project/sqlalchemy-filters/
            if conditions:
                clauses = []
                for c in conditions:
                    f, o, v = c
                    if o == 'lt':
                        clauses.append(Guest.__table__.c[f] < v)
                    elif o == 'lte':
                        clauses.append(Guest.__table__.c[f] <= v)
                    elif o == 'eq':
                        clauses.append(Guest.__table__.c[f] == v)
                    elif o == 'ne':
                        clauses.append(Guest.__table__.c[f] != v)
                    elif o == 'gte':
                        clauses.append(Guest.__table__.c[f] >= v)
                    elif o == 'gt':
                        clauses.append(Guest.__table__.c[f] > v)
                if operator == 'or':
                    query = query.filter(or_(*clauses))
                else:
                    query = query.filter(and_(*clauses))

            if direction == 'asc':
                query = query.order_by(
                    Guest.__table__.columns[criteria].asc())
            else:
                query = query.order_by(
                    Guest.__table__.columns[criteria].desc())

            if search:
                query = query.filter(
                    or_(
                        Guest.name.ilike(search),
                        Guest.surname.ilike(search),
                        Guest.email.ilike(search),
                        Guest.address1.ilike(search),
                        Guest.address2.ilike(search),
                        Guest.address1.ilike(search),
                        Guest.locality.ilike(search),
                        Guest.postcode.ilike(search),
                        Guest.province.ilike(search),
                        Guest.home_phone.ilike(search),
                        Guest.mobile_phone.ilike(search)))

            # Calculate limit and offset
            limit = size
            offset = size * (page - 1)
            query = query.offset(offset)
            query = query.limit(limit)

            # Execute query
            result = query.all()

            # Return result
            self.response.payload[:] = result if result else []


class Bookings(Service):
    """Service class to get a list of all bookings from a guest."""
    """Includes the guest details and the list of bookings and rooms."""
    """Channel /genesisng/guests/{id}/bookings."""

    class SimpleIO:
        input_required = (Integer('id'))
        output_required = ('id', 'name', 'surname', 'gender', 'email')
        output_optional = ('passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone',
                           ListOfDicts('bookings'), ListOfDicts('rooms'))
        skip_empty_keys = True

    def handle(self):
        id_ = self.request.input.id

        result = {}

        # Get guest data
        input_data = {'id': id_}
        guest = self.invoke('guest.get', input_data)
        if guest:
            result = guest['response']

        # Get the list of bookings from the guest
        result['bookings'] = []
        input_data = {
            'filters': ['id_guest|eq|%s' % id_]
        }
        bookings = self.invoke('booking.list', input_data)

        if bookings:
            rooms = []
            for b in bookings['response']:
                del b['count']
                result['bookings'].append(b)
                rooms.append(b['id_room'])

        # Get room data
        # room.list does not support OR on multiple filters at the moment
        result['rooms'] = []
        for r in rooms:
            input_data = {'id': '%d' % r}
            room = self.invoke('room.get', input_data)
            if room:
                result['rooms'].append(room['response'])

        # Return dictinary with guest, bookings and rooms
        if result:
            self.response.status_code = OK
            self.response.payload = result
        else:
            self.response.status_code = NOT_FOUND
            self.response.payload = ''


class Restore(Service):
    """Service class to restore a deleted an existing guest."""
    """Channel /genesisng/guests/{id}/restore"""

    class SimpleIO:
        input_required = (Integer('id'))
        output_required = ('id', 'name', 'surname', 'gender', 'email')
        output_optional = ('passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Guest).\
                filter(and_(Guest.id == id_, Guest.deleted.isnot(None))).\
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
