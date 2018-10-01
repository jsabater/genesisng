# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service, Integer, Date, DateTime
from genesisng.schema.guest import Guest
from genesisng.schema.booking import Booking
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from urlparse import parse_qs
from datetime import datetime


class Get(Service):
    """Service class to get a guest by id."""
    """Channel /genesisng/guests/{id}/details."""

    class SimpleIO(object):
        input_required = ('id')
        output_optional = ('id', 'name',
                           'surname', 'gender', 'email', 'passport',
                           Date('birthdate'), 'address1', 'address2',
                           'locality', 'postcode', 'province', 'country',
                           'home_phone', 'mobile_phone', DateTime('deleted'))

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        self.logger.info("Executing /genesisng/guests/{id}/details")

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
        input_required = ('name', 'surname', 'gender', 'email', 'passport',
                          'address1', 'locality', 'postcode', 'province',
                          'country')
        input_optional = ('address2', 'birthdate', 'home_phone',
                          'mobile_phone')
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', 'birthdate', 'address1', 'address2',
                           'locality', 'postcode', 'province', 'country',
                           'home_phone', 'mobile_phone', 'deleted')

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
                self.response.headers['Location'] = url.format(id, guest.id)

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

        self.logger.info("Deleting guest with id: %s" % id_)

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
        input_required = ('id')
        input_optional = ('name', 'surname', 'gender', 'email', 'passport',
                          'birthdate', 'address1', 'address2', 'locality',
                          'postcode', 'province', 'country', 'home_phone',
                          'mobile_phone')
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', 'birthdate', 'address1', 'address2',
                           'locality', 'postcode', 'province', 'country',
                           'home_phone', 'mobile_phone', 'deleted')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input
        guest = Guest(
            id=id_,
            name=p.name,
            surname=p.surname,
            gender=p.gender,
            email=p.email,
            passport=p.passport,
            birthdate=p.birthdate,
            address1=p.address1,
            address2=p.address2,
            locality=p.locality,
            postcode=p.postcode,
            province=p.province,
            country=p.country,
            home_phone=p.home_phone,
            mobile_phone=p.mobile_phone)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Guest).\
                filter(and_(Guest.id == id_, Guest.deleted.is_(None))).\
                one_or_none()

            if result:
                # Update dictionary keys
                result.name = guest.name
                result.surname = guest.surname
                result.surname = guest.guestender
                result.email = guest.email
                result.passport = guest.passport
                result.birthdate = guest.birthdate
                result.address1 = guest.address1
                result.address2 = guest.address2
                result.locality = guest.locality
                result.postcode = guest.postcode
                result.province = guest.province
                result.country = guest.country
                result.home_phone = guest.home_phone
                result.mobile_phone = guest.mobile_phone
                session.commit()
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class List(Service):
    """Service class to get a list of all guests in the system."""
    """Channel /genesisng/guests/list."""

    class SimpleIO:
        input_optional = ('page', 'size', 'sort_by', 'order_by', 'filters',
                          'search', 'fields')
        output_optional = ('count', 'id', 'name', 'surname', 'gender', 'email',
                           'passport', 'birthdate', 'address1', 'address2',
                           'locality', 'postcode', 'province', 'country',
                           'home_phone', 'mobile_phone', 'deleted')
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
    """Channel /genesisng/guests/{id}/bookings."""

    class SimpleIO:
        input_required = ('id')
        output_optional = ('count', 'id', 'id_guest', 'id_room',
                           DateTime('reserved'), 'guests', Date('check_in'),
                           Date('check_out'), DateTime('checked_in'),
                           DateTime('checked_out'), DateTime('cancelled'),
                           'base_price', 'taxes_percentage', 'taxes_value',
                           'total_price', 'locator', 'pin', 'status',
                           'meal_plan', 'additional_services', 'uuid',
                           'deleted')
        output_repeated = True
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        self.logger.info("Executing /genesisng/guests/{id}/bookings")

        # Execute query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))
            query = query.add_entity(Booking)
            query = query.filter(
                and_(Guest.id == Booking.id_guest, Guest.deleted.is_(None),
                     Booking.id_guest == id_))
            result = query.all()
            for r in result:
                self.logger.info(r)
            self.response.payload[:] = result if result else []
