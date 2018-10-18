# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service
from zato.server.service import Integer, Date, DateTime, ListOfDicts
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

    class SimpleIO:
        input_optional = (Integer('page'), Integer('size'), 'sort_by',
                          'order_by', 'filters', 'search', 'fields')
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

        # Search is optional
        search = None

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
                if order_by not in ('id', 'name', 'surname', 'gender', 'email',
                                    'birthdate', 'country'):
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
                    if field not in ('id', 'name', 'surname', 'gender',
                                     'email', 'passport', 'birthdate',
                                     'address1', 'address2', 'locality',
                                     'postcode', 'province', 'country',
                                     'home_phone', 'mobile_phone'):
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

            # Handle search
            try:
                search = qs['search'][0]
            except (ValueError, KeyError):
                # Do not search for terms instead of returning 400 Bad Request
                pass

            # Handle fields projection
            try:
                for field in qs['fields']:
                    if field not in ('id', 'name', 'surname', 'gender',
                                     'email', 'passport', 'birthdate',
                                     'address1', 'address2', 'locality',
                                     'postcode', 'province', 'country',
                                     'home_phone', 'mobile_phone', 'deleted'):
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
                conditions.append(Guest.__table__.columns[field] < value)
            elif operator == 'lte':
                conditions.append(Guest.__table__.columns[field] <= value)
            elif operator == 'eq':
                conditions.append(Guest.__table__.columns[field] == value)
            elif operator == 'ne':
                conditions.append(Guest.__table__.columns[field] != value)
            elif operator == 'gte':
                conditions.append(Guest.__table__.columns[field] >= value)
            elif operator == 'gt':
                conditions.append(Guest.__table__.columns[field] > value)

        # Prepare search
        if search:
            term = '%' + search + '%'

        # Prepare fields projection
        columns = []
        if not fields:
            fields = ('id', 'name', 'surname', 'gender', 'email', 'passport',
                      'birthdate', 'address1', 'address2', 'locality',
                      'postcode', 'province', 'country', 'home_phone',
                      'mobile_phone', 'deleted')
        columns = [Guest.__table__.columns[f] for f in fields]

        # Execute query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))
            for c in columns:
                query = query.add_columns(c)
            for c in conditions:
                query = query.filter(c)
            if search:
                query = query.filter(
                    or_(
                        Guest.name.ilike(term), Guest.surname.ilike(term),
                        Guest.email.ilike(term), Guest.address1.ilike(term),
                        Guest.address2.ilike(term), Guest.address1.ilike(term),
                        Guest.locality.ilike(term), Guest.postcode.ilike(term),
                        Guest.province.ilike(term),
                        Guest.home_phone.ilike(term),
                        Guest.mobile_phone.ilike(term)))
            if direction == 'asc':
                query = query.order_by(Guest.__table__.columns[criteria].asc())
            else:
                query = query.order_by(
                    Guest.__table__.columns[criteria].desc())
            query = query.offset(offset)
            query = query.limit(limit)
            result = query.all()
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
        # guest.list does not support OR on multiple filters at the moment
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
