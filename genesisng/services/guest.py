# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT, BAD_REQUEST
from zato.server.service import Service
from zato.server.service import Integer, Date, DateTime, ListOfDicts
from zato.server.service import Dict, List
from genesisng.schema.guest import Guest
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime


class Get(Service):
    """
    Service class to get a guest by id.

    Channel ``/genesisng/guests/{id}/get``

    Uses `SimpleIO`_.

    Stores the record in the ``guests`` cache. Returns ``Cache-Control``,
    ``Last-Modified`` and ``ETag`` headers.

    Returns ``OK`` upon successful retrieval, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO(object):
        input_required = (Integer('id'))
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone', 'fullname')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the guest
        :type id: int

        :returns: All attributes of a :class:`~genesisng.schema.guest.Guest`
            model class, including the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        id_ = self.request.input.id

        # Check whether a copy exists in the cache
        cache_key = 'id:%s' % id_
        cache = self.cache.get_cache('builtin', 'guests')
        cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.payload = cache_data.value
            return

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Guest).\
                filter(and_(Guest.id == id_, Guest.deleted.is_(None))).\
                one_or_none()

            if result:

                # Save the record in the cache
                cache_data = cache.set(
                    cache_key, result.asdict(), details=True)

                # Set cache headers in response
                if cache_data:
                    self.response.headers['Cache-Control'] = cache_control
                    self.response.headers['Last-Modified'] = cache_data.\
                        last_write_http
                    self.response.headers['ETag'] = cache_data.hash
                else:
                    self.response.headers['Cache-Control'] = 'no-cache'

                # Return the result
                self.response.status_code = OK
                self.response.headers['Content-Language'] = 'en'
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'


class Create(Service):
    """
    Service class to create a new guest.

    Channel ``/genesisng/guests/create``.

    Uses `SimpleIO`_.

    Stores the record in the ``guests`` cache. Returns a ``Cache-Control``
    header.

    Returns ``CREATED`` upon successful creation, or ``CONFLICT`` otherwise.
    """

    class SimpleIO:
        input_required = ('name', 'surname', 'email')
        input_optional = ('gender', 'passport', Date('birthdate'), 'address1',
                          'address2', 'locality', 'postcode', 'province',
                          'country', 'home_phone', 'mobile_phone')
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param name: The first name of the guest.
        :type name: str
        :param surname: The last name of the guest.
        :type surname: str
        :param gender: The gender of the guest.
        :type gender: enum
        :param email: The electronic mail address of the guest.
        :type email: str
        :param passport: The passport number, tax id or similar identification
            number.
        :type passport: str
        :param address1: The postal address of the guest.
        :type address1: str
        :param address2: Additional information of the postal address.
        :type address2: str
        :param locality: The city, town or similar.
        :type locality: str
        :param postcode: The postal code.
        :type postcode: str
        :param province: The province, county, state or similar.
        :type province: str
        :param home_phone: The home phone number.
        :type home_phone: str
        :param mobile_phone: The mobile phone number.
        :type mobile_phone: str

        :returns: All attributes of a :class:`~genesisng.schema.guest.Guest`
            model class.
        :rtype: dict
        """

        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        result = Guest(
            name=p.name,
            surname=p.surname,
            gender=p.get('gender', 'Male'),
            email=p.email,
            passport=p.passport,
            birthdate=p.get('birthdate', None),
            address1=p.address1,
            address2=p.get('address2', None),
            locality=p.locality,
            postcode=p.postcode,
            province=p.province,
            country=p.country,
            home_phone=p.get('home_phone', None),
            mobile_phone=p.get('mobile_phone', None))

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(result)
                session.commit()

                # Save the record in the cache
                cache_key = 'id:%s' % result.id
                cache = self.cache.get_cache('builtin', 'guests')
                result = result.asdict()
                cache.set(cache_key, result)

                # Return the result
                self.response.status_code = CREATED
                self.response.payload = result
                url = self.user_config.genesisng.location.guests
                self.response.headers['Location'] = url.format(id=result['id'])
                self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraint prevents duplication of emails.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class Delete(Service):
    """
    Service class to delete an existing guest.

    Channel ``/genesisng/guests/{id}/delete``.

    Uses `SimpleIO`_.

    Removes the record from the ``guests`` cache, if found. Returns a
    ``Cache-Control`` header.

    Returns ``NO_CONTENT`` upon successful deletion, or ``NOT_FOUND``
    therwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        """
        Service handler.

        :param id: The id of the guest.
        :type id: int

        :returns: Nothing.
        """

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
                self.response.headers['Cache-Control'] = 'no-cache'

                # Invalidate the cache
                cache_key = 'id:%s' % id_
                cache = self.cache.get_cache('builtin', 'guests')
                cache.delete(cache_key)

            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Update(Service):
    """
    Service class to update an existing guest.

    Channel ``/genesisng/guests/{id}/update``.

    Uses `SimpleIO`_.

    Stores the updated record in the ``guests`` cache. Returns a
    ``Cache-Control`` header. Only non-empty keys will be updated.

    Returns ``OK`` upon successful modification, ``NOT_FOUND`` if the record
    cannot be found, or ``CONFLICT`` in case of a constraint error.

    Attributes not sent through the request are not updated.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = ('name', 'surname', 'gender', 'email', 'passport',
                          Date('birthdate'), 'address1', 'address2',
                          'locality', 'postcode', 'province', 'country',
                          'home_phone', 'mobile_phone')
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the guest. Mandatory.
        :type id: int
        :param name: The first name of the guest.
        :type name: str
        :param surname: The last name of the guest.
        :type surname: str
        :param gender: The gender of the guest.
        :type gender: enum
        :param email: The electronic mail address of the guest.
        :type email: str
        :param passport: The passport number, tax id or similar identification
            number.
        :type passport: str
        :param address1: The postal address of the guest.
        :type address1: str
        :param address2: Additional information of the postal address.
        :type address2: str
        :param locality: The city, town or similar.
        :type locality: str
        :param postcode: The postal code.
        :type postcode: str
        :param province: The province, county, state or similar.
        :type province: str
        :param home_phone: The home phone number.
        :type home_phone: str
        :param mobile_phone: The mobile phone number.
        :type mobile_phone: str

        :returns: All attributes of a :class:`~genesisng.schema.guest.Guest`
            model class.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                result = session.query(Guest).\
                    filter(and_(Guest.id == id_, Guest.deleted.is_(None))).\
                    one_or_none()

                if result:
                    # TODO: Implement a wrapper to remove empty request keys,
                    # or add request params to skip_empty_keys as per
                    # https://forum.zato.io/t/leave-the-simpleio-input-optional-out-of-the-input/593/22
                    # then use dictalchemy's .fromdict() to reduce code.
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

                    # Save the record in the cache
                    cache_key = 'id:%s' % result.id
                    cache = self.cache.get_cache('builtin', 'guests')
                    cache_data = cache.set(
                        cache_key, result.asdict(), details=True)

                    self.response.status_code = OK
                    self.response.payload = result
                    self.response.headers['Cache-Control'] = 'no-cache'
                else:
                    self.response.status_code = NOT_FOUND
                    self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraint prevents duplication of emails.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class Upsert(Service):
    """
    Service class to insert or update a guest in the system.

    Channel ``/genesisng/guests/upsert``.

    Uses `SimpleIO`_.

    If there was an existing user but it was deleted, it is restored.

    Stores the record in the ``guests`` cache. Returns a ``Cache-Control``
    header.

    Returns ``OK`` upon successful creation or update, or ``CONFLICT``
    otherwise.
    """

    class SimpleIO:
        input_required = ('name', 'surname', 'email')
        input_optional = ('gender', 'passport', Date('birthdate'), 'address1',
                          'address2', 'locality', 'postcode', 'province',
                          'country', 'home_phone', 'mobile_phone')
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone',
                           Dict('error'))
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param name: The first name of the guest.
        :type name: str
        :param surname: The last name of the guest.
        :type surname: str
        :param gender: The gender of the guest.
        :type gender: enum
        :param email: The electronic mail address of the guest.
        :type email: str
        :param passport: The passport number, tax id or similar identification
            number.
        :type passport: str
        :param address1: The postal address of the guest.
        :type address1: str
        :param address2: Additional information of the postal address.
        :type address2: str
        :param locality: The city, town or similar.
        :type locality: str
        :param postcode: The postal code.
        :type postcode: str
        :param province: The province, county, state or similar.
        :type province: str
        :param home_phone: The home phone number.
        :type home_phone: str
        :param mobile_phone: The mobile phone number.
        :type mobile_phone: str
        :param session: A live session (transaction) to be reused.
        :type session: :class:`~sqlalchemy.orm.session.Session`

        :returns: All attributes of a :class:`~genesisng.schema.guest.Guest`
            model class.
        :rtype: dict
        """

        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection
        p = self.request.input

        try:
            if p.birthdate:
                datetime.strptime(p.birthdate, '%Y-%m-%d').date()
        except ValueError:
            self.response.status_code = BAD_REQUEST
            msg = 'Wrong birthdate format.'
            self.response.payload = {'error': {'message': msg}}
            return

        params = {
            'name': p.name,
            'surname': p.surname,
            'gender': p.gender,
            'email': p.email,
            'passport': p.passport,
            'birthdate': p.birthdate,
            'address1': p.address1,
            'address2': p.address2,
            'locality': p.locality,
            'postcode': p.postcode,
            'province': p.province,
            'country': p.country,
            'home_phone': p.home_phone,
            'mobile_phone': p.mobile_phone,
            'deleted': None
        }

        # Remove empty strings from params
        for k in params.keys():
            if params[k] == '':
                del(params[k])

        # Reuse the session if any has been provided
        if self.environ.session:
            session = self.environ.session
        else:
            session = self.outgoing.sql.get(conn).session()

        # INSERT .. ON CONFLICT DO UPDATE is not well supported by the
        # current version of SQLAlchemy (1.3), so we do it manually.
        result = session.query(Guest).\
            filter(Guest.email == p.email).one_or_none()

        try:
            if result:
                # Update the record
                result.fromdict(params)
            else:
                # Add a new record
                result = Guest().fromdict(params)
                session.add(result)

            # Flush if we are reusing the session, otherwise commit
            if self.environ.session:
                session.flush()
            else:
                session.commit()

            # Save the record in the cache only if the session was new
            cache_key = 'id:%s' % result.id
            cache = self.cache.get_cache('builtin', 'guests')
            cache.set(cache_key, result.asdict())

            # Return the result
            self.environ.status = OK
            self.response.status_code = OK
            self.response.payload = result
            url = self.user_config.genesisng.location.guests
            self.response.headers['Location'] = url.format(id=result.id)
            self.response.headers['Cache-Control'] = 'no-cache'

        except IntegrityError:
            # Constraint prevents duplication of emails.
            # Given the nature of this service, this situation should never be
            # reached.
            session.rollback()
            self.response.status_code = CONFLICT
            self.environ.status = CONFLICT
            self.response.headers['Cache-Control'] = 'no-cache'
            # TODO: Return well-formed error response
            # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948

        # Close the session only if we created a new one
        if not self.environ.session:
            session.close()


class List(Service):
    """
    Service class to get a list of guests in the system.

    Channel ``/genesisng/guests/list``.

    Uses `SimpleIO`_.

    Stores the returned records in the ``guests`` cache. Returns a
    ``Cache-Control`` header.

    Returns ``NO_CONTENT`` if the returned list is empty, or ``OK`` otherwise.

    Pagination and sorting are always enforced. Filtering is optional. Multiple
    filters are allowed but only one operator for all the filters. Fields
    projection is allowed. Search is optional and the passed search term is
    case insensitive.

    In case of error, it does not return ``BAD_REQUEST`` but, instead, it
    assumes the default parameter values and carries on.

    Includes the count of records returned.
    """

    criteria_allowed = ('id', 'name', 'surname', 'gender', 'email',
                        'birthdate', 'country')
    direction_allowed = ('asc', 'desc')
    filters_allowed = ('id', 'name', 'surname', 'gender', 'email', 'passport',
                       'birthdate', 'address1', 'address2', 'locality',
                       'postcode', 'province', 'country', 'home_phone',
                       'mobile_phone')
    comparisons_allowed = ('lt', 'lte', 'eq', 'ne', 'gte', 'gt')
    operators_allowed = ('and', 'or')
    fields_allowed = ('id', 'name', 'surname', 'gender', 'email', 'passport',
                      'birthdate', 'address1', 'address2', 'locality',
                      'postcode', 'province', 'country', 'home_phone',
                      'mobile_phone', 'deleted')
    search_allowed = ('id', 'name', 'surname', 'gender', 'email', 'passport',
                      'birthdate', 'address1', 'address2', 'locality',
                      'postcode', 'province', 'country', 'home_phone',
                      'mobile_phone', 'deleted')

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('operator'), List('search'))
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone',
                           DateTime('deleted'), 'count')
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        """
        Service handler.

        Query string parameters:

        :param page: The page number. Default is 1.
        :type page: int
        :param size: The page size. Default is located in the user config.
        :type size: int
        :param sort: The sort criteria (field name) and direction (ascending
            ``asc`` or descending ``desc``), using the pipe ``|`` as separator
            (i.e. ``<criteria>|<direction>``. The default criteria is ``id``
            and the default direction is ``asc``, so the default value of this
            paramter is ``id|asc``.
        :type sort: str
        :param filters: A filter to process the data stream to produce the
            desired output. Each filter is made of a field name, a comparator
            and a value, using the pipe ``|`` as separator (i.e.
            ``<field>|<comparator>|<value>``). Multiple occurrences of this
            parameter are allowed. Supported comparators are ``lt`` (less
            than), ``lte`` (less than or equal), ``eq`` (equal), ``ne`` (not
            equal), ``gte`` (greater than or equal) and ``gt`` (greater than).
        :type filters: str
        :param operator: The operator to apply to or join all filters. The
            supported operators are ``and`` and ``or``. The default value is
            ``and``.
        :type operator: str
        :param fields: Fields projection. A field name of the model class.
            Multiple occurrences of this parameter are allowed. Supported
            fields are all in the :class:`~genesisng.schema.guest.Guest` model
            class.
        :type fields: str
        :param search: Search term (case insensitive). The passed term will be
            searched using pattern-matching indexes in the all fields.
        :type search: str

        :returns: A list of dicts with all attributes of a
            :class:`~genesisng.schema.guest.Guest` model class, minus the
            ``fullname`` hybrid attribute.
        :rtype: list
        """

        conn = self.user_config.genesisng.database.connection
        default_page_size = int(
            self.user_config.genesisng.pagination.default_page_size)
        max_page_size = int(
            self.user_config.genesisng.pagination.max_page_size)
        cols = Guest.__table__.columns

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
                query = query.add_columns(cols[c])

            # Prepare filters
            if conditions:
                clauses = []
                for c in conditions:
                    f, o, v = c
                    if o == 'lt':
                        clauses.append(cols[f] < v)
                    elif o == 'lte':
                        clauses.append(cols[f] <= v)
                    elif o == 'eq':
                        clauses.append(cols[f] == v)
                    elif o == 'ne':
                        clauses.append(cols[f] != v)
                    elif o == 'gte':
                        clauses.append(cols[f] >= v)
                    elif o == 'gt':
                        clauses.append(cols[f] > v)
                if operator == 'or':
                    query = query.filter(or_(*clauses))
                else:
                    query = query.filter(and_(*clauses))

            # Search
            if search:
                clauses = []
                for s in self.search_allowed:
                    clauses.append(cols[s].ilike(search))
                query = query.filter(or_(*clauses))

            # Order by
            if direction == 'asc':
                query = query.order_by(cols[criteria].asc())
            else:
                query = query.order_by(cols[criteria].desc())

            # Calculate limit and offset
            limit = size
            offset = size * (page - 1)
            query = query.offset(offset)
            query = query.limit(limit)

            # Execute query
            result = query.all()

            # Return result
            if result:
                # Store results in the cache only if all fields were retrieved
                if not fields:
                    cache = self.cache.get_cache('builtin', 'guests')
                    for r in result:
                        # Items are already dictionaries.
                        cache_key = 'id:%s' % r.id
                        cache.set(cache_key, r)

                self.response.status_code = OK
                self.response.payload[:] = result
                self.response.headers['Cache-Control'] = 'no-cache'
            else:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'


class Bookings(Service):
    """
    Service class to get a list of all bookings from a guest.

    Channel ``/genesisng/guests/{id}/bookings``.

    Uses `SimpleIO`_.

    Includes the guest details and the list of bookings and rooms.

    Returns ``OK`` if the guest was found, even if he/she had no bookings, or
    ``NOT_FOUND`` otherwise.

    Invokes the services :class:`~genesisng.services.guest.Get`,
    :class:`~genesisng.services.bookings.List` and
    :class:`~genesisng.services.rooms.List` to retrieve the required data.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone',
                           ListOfDicts('bookings'), ListOfDicts('rooms'))
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the guest
        :type id: int

        :returns: All attributes of a :class:`~genesisng.schema.guest.Guest`
            model class, including the hybrid properties. A list of dicts
            under the ``booking`` key with all bookings, and a list of dicts
            under the ``room`` key with all the rooms in such bookings, without
            duplicates.
        :rtype: dict
        """
        id_ = self.request.input.id

        result = {}

        # Get guest data
        input_data = {'id': id_}
        guest = self.invoke('guest.get', input_data)

        if guest['response']:
            # Add the guest to the result
            result = guest['response']

            # Store the result in the cache
            # Result is already a dict
            cache = self.cache.get_cache('builtin', 'guests')
            cache_key = 'id:%s' % guest['response']['id']
            cache.set(cache_key, guest['response'])

            # Get the list of bookings from the guest
            result['bookings'] = []
            input_data = {'filters': ['id_guest|eq|%s' % id_]}
            bookings = self.invoke('booking.list', input_data)

            room_ids = []
            if bookings['response']:
                cache = self.cache.get_cache('builtin', 'bookings')
                for b in bookings['response']:

                    # Add the booking to the result
                    del b['count']
                    result['bookings'].append(b)

                    # Save the room id in the booking
                    room_ids.append(b['id_room'])

                    # Store booking in the cache
                    # Result is already a dict
                    cache_key = 'id:%s' % b['id']
                    cache.set(cache_key, b)

            # Get room data from the list of saved rooms
            result['rooms'] = []
            if room_ids:
                input_data = {'operator': 'or', 'filters': []}
                for i in room_ids:
                    input_data['filters'].append('id|eq|%d' % i)
                rooms = self.invoke('room.list', input_data)
                if rooms['response']:
                    cache = self.cache.get_cache('builtin', 'rooms')
                    for r in rooms['response']:

                        # Add the room to the result
                        del r['count']
                        result['rooms'].append(r)

                        # Store room in the cache
                        # Result is already a dict
                        cache_key = 'id:%s' % r['id']
                        cache.set(cache_key, r)

        # Return the dictionary with guest, bookings and rooms
        if result:
            self.response.status_code = OK
            self.response.payload = result
            self.response.headers['Cache-Control'] = 'no-cache'
        else:
            self.response.status_code = NOT_FOUND
            self.response.headers['Cache-Control'] = 'no-cache'


class Restore(Service):
    """
    Service class to restore a deleted guest.

    Channel ``/genesisng/guests/{id}/restore``.

    Uses `SimpleIO`_.

    Sets the ``deleted`` field to None if, and only if, the guest exists and it
    had been previously marked as deleted.

    Stores the record in the ``guests`` cache. Returns a ``Cache-Control``
    header.

    Returns ``OK`` upon successful restoration, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        output_optional = ('id', 'name', 'surname', 'gender', 'email',
                           'passport', Date('birthdate'), 'address1',
                           'address2', 'locality', 'postcode', 'province',
                           'country', 'home_phone', 'mobile_phone')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the guest.
        :type id: int

        :returns: All attributes of a :class:`~genesisng.schema.guest.Guest`
            model class.
        :rtype: dict
        """

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

                # Save the result in the cache, as dict
                cache_key = 'id:%s' % id_
                cache = self.cache.get_cache('builtin', 'guests')
                result = result.asdict()
                cache.set(cache_key, result)

                self.response.status_code = OK
                self.response.payload = result
                self.response.headers['Cache-Control'] = 'no-cache'
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'
