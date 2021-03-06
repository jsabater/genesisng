# -*- coding: utf-8 -*-
from contextlib import closing
from http.client import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT, FORBIDDEN
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import undefer
from passlib.hash import bcrypt
from bunch import Bunch
from zato.server.service import Service, Boolean, Integer, AsIs, List
from genesisng.schema.login import Login
from genesisng.util.config import parse_args
from genesisng.util.filters import parse_filters


class Get(Service):
    """
    Service class to get a login by id.

    Channel ``/genesisng/logins/{id}/get``.

    Uses `SimpleIO`_ and `JSON Schema`_.

    The password is never sent back to the client side.

    Stores the record in the ``logins`` cache (minus the password). Returns
    ``Cache-Control``, ``Last-Modified`` and ``ETag`` headers.

    Returns ``OK`` upon successful retrieval, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        # Passwords never travel back to the client side
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the user.
        :type id: int

        :returns: All attributes of a :class:`~genesisng.schema.login.Login`
            model class, minus the password.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        id_ = self.request.input.id

        # Check whether a copy exists in the cache
        cache_key = 'id:%s' % id_
        cache = self.cache.get_cache('builtin', 'logins')
        cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.payload = cache_data.value
            self.logger.info('Cache data value contains: %s' %
                             cache_data.value)
            return

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).filter(Login.id == id_).one_or_none()

            if result:

                # Save the record in the cache, minus the password
                result = result.asdict(exclude=['password'])
                cache_data = cache.set(cache_key, result, details=True)
                self.logger.info('Cache data value set to: %s' %
                                 cache_data.value)

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


class Validate(Service):
    """
    Service class to validate credentials.

    Channel ``/genesisng/logins/validate``.

    Uses `SimpleIO`_.

    Stores the record in the ``logins`` cache (minus the password). Returns a
    ``Cache-Control`` header.

    Returns ``OK`` upon successful validation, or ``FORBIDDEN`` otherwise.

    Depending on the config value ``security.login_validation``, it uses the
    database cryptographic functions to verify the password or it verifies it
    inside the service. The former is faster but the clear-text passwords
    travels to the database.
    """

    class SimpleIO:
        input_required = ('username', AsIs('password'))
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param username: The username of the user.
        :type username: str
        :param password: The password of the user.
        :type password: str

        :returns: All attributes of a :class:`~genesisng.schema.login.Login`
            model class, minus the password.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        vtype = self.user_config.genesisng.security.login_validation_type
        username = self.request.input.username
        password = self.request.input.password

        with closing(self.outgoing.sql.get(conn).session()) as session:

            result = None
            if vtype == 'database':
                # Send the clear-text password to the database for verification
                result = session.query(Login).\
                    filter(and_(Login.username == username,
                                Login.password == password)).\
                    one_or_none()
            else:
                # Do not send the clear-text password to the database. Instead,
                # verify it inside the service.
                result = session.query(Login).options(undefer('_password')).\
                    filter(Login.username == username).one_or_none()
                if result:
                    if not bcrypt.verify(password, result.password):
                        result = None

            if result:

                # Save the record in the cache, minus the password
                cache_key = 'id-%s' % result.id
                cache = self.cache.get_cache('builtin', 'logins')
                result = result.asdict(exclude=['password'])
                cache.set(cache_key, result)

                self.response.status_code = OK
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.payload = result
            else:
                self.response.status_code = FORBIDDEN
                self.response.headers['Cache-Control'] = 'no-cache'


class Create(Service):
    """
    Service class to create a new login.

    Channel ``/genesisng/logins/create``.

    Uses `SimpleIO`_.

    Stores the record in the ``logins`` cache (minus the password). Returns a
    ``Cache-Control`` header.

    Returns ``CREATED`` upon successful creation, or ``CONFLICT`` otherwise.
    """

    class SimpleIO:
        input_required = ('username', AsIs('password'))
        input_optional = ('name', 'surname', 'email',
                          Boolean('is_admin', default=False))
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param username: The username of the user.
        :type username: str
        :param password: The password of the user.
        :type password: str
        :param name: The name of the user.
        :type name: str
        :param surname: The surname of the user.
        :type surname: str
        :param email: The electronic mail address of the user.
        :type email: str
        :param is_admin: Is the user an administrator? Default is False.
        :type is_admin: bool

        :returns: All attributes of a :class:`~genesisng.schema.login.Login`
            model class, minus the password.
        :rtype: dict

        .. todo:: Use `Cerberus`_ to validate input?
        .. todo:: Return a well-formed `error response`_.
        """

        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        result = Login(
            username=p.username,
            password=p.password,
            name=p.name,
            surname=p.surname,
            email=p.email,
            is_admin=p.get('is_admin', False))

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(result)
                session.commit()

                # Save the record in the cache, minus the password
                cache_key = 'id:%s' % result.id
                cache = self.cache.get_cache('builtin', 'logins')
                cache.set(cache_key, result.asdict(exclude=['password']))

                # Return the result
                self.response.status_code = CREATED
                self.response.payload = result
                url = self.user_config.genesisng.location.logins
                self.response.headers['Location'] = url.format(id=result.id)
                self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraint prevents duplication of username or emails.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'


class Delete(Service):
    """
    Service class to delete an existing login.

    Channel ``/genesisng/logins/{id}/delete``.

    Uses `SimpleIO`_.

    Removes the record from the ``logins`` cache, if found. Returns a
    ``Cache-Control`` header.

    Returns ``NO_CONTENT`` upon successful deletion, or ``NOT_FOUND``
    therwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        """
        Service handler.

        :param id: The id of the user.
        :type id: int

        :returns: Nothing.
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            deleted = session.query(Login).filter(Login.id == id_).delete()
            session.commit()

            if deleted:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'

                # Invalidate the cache
                cache_key = 'id:%s' % id_
                cache = self.cache.get_cache('builtin', 'logins')
                cache.delete(cache_key)

            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Update(Service):
    """
    Service class to update an existing login.

    Channel ``/genesisng/logins/{id}/update``.

    Uses `SimpleIO`_.

    Stores the updated record in the ``logins`` cache (minus the password).
    Returns a ``Cache-Control`` header. Only non-empty keys will be updated.

    Returns ``OK`` upon successful modification, ``NOT_FOUND`` if the record
    cannot be found, or ``CONFLICT`` in case of a constraint error.

    Attributes not sent through the request are not updated.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = ('username', AsIs('password'), 'name', 'surname',
                          'email', Boolean('is_admin', default=False))
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the user. Mandatory.
        :type id: int
        :param username: The username of the user.
        :type username: str
        :param password: The password of the user.
        :type password: str
        :param name: The name of the user.
        :type name: str
        :param surname: The surname of the user.
        :type surname: str
        :param email: The electronic mail address of the user.
        :type email: str
        :param is_admin: Is the user an administrator?
        :type is_admin: bool

        :returns: All attributes of a :class:`~genesisng.schema.login.Login`
            model class, minus the password.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                result = session.query(Login).filter(Login.id == id_).\
                    one_or_none()

                if result:
                    # TODO: Implement a wrapper to remove empty request keys,
                    # or add request params to skip_empty_keys as per
                    # https://forum.zato.io/t/leave-the-simpleio-input-optional-out-of-the-input/593/22
                    # then use dictalchemy's .fromdict() to reduce code.
                    # result.fromdict(self.request.input, allow_pk=True)

                    # Update dictionary keys
                    if p.username:
                        result.username = p.username
                    if p.password:
                        result.password = p.password
                    if p.name:
                        result.name = p.name
                    if p.surname:
                        result.surname = p.surname
                    if p.email:
                        result.email = p.email
                    if p.is_admin != '':
                        result.is_admin = p.is_admin
                    session.commit()

                    # Save the record in the cache, minus the password
                    cache_key = 'id:%s' % result.id
                    cache = self.cache.get_cache('builtin', 'logins')
                    cache.set(cache_key, result.asdict())

                    # Return the result
                    self.response.status_code = OK
                    self.response.payload = result
                    self.response.headers['Cache-Control'] = 'no-cache'
                else:
                    self.response.status_code = NOT_FOUND
                    self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraint prevents duplication of username or emails.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class List(Service):
    """
    Service class to get a list of logins in the system.

    Channel ``/genesisng/logins/list``.

    Uses `SimpleIO`_.

    Stores the returned record set and each of the records individually in the
    ``logins`` cache (minus the password). The set is the whole page and is
    reused when going back and forth through pages. Individual records are used
    by the ``Get`` service. Returns a ``Cache-Control`` header.

    Returns ``NO_CONTENT`` if the returned list is empty, or ``OK`` otherwise.

    Pagination and sorting are always enforced. Filtering is optional. Multiple
    filters are allowed but only one operator for all the filters. Fields
    projection is allowed. Search is optional and the passed search term is
    case insensitive.

    In case of error, it does not return ``BAD_REQUEST`` but, instead, it
    assumes the default parameter values and carries on.

    The total count of records (``X-Genesis-Count``), the page number
    (``X-Genesis-Page``) and the page size (``X-Genesis-Size``) are returned as
    headers.
    """

    # Fields allowed in sorting criteria, filters, field projection or
    # searched in.
    allowed = Bunch({
        'criteria': ('id', 'username', 'name', 'surname', 'email'),
        'filters': ('id', 'username', 'name', 'surname', 'email', 'is_admin'),
        'fields': ('id', 'username', 'name', 'surname', 'email', 'is_admin'),
        'search': ('username', 'name', 'surname', 'email')
    })

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('fields'), List('operator'),
                          List('search'))
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin', 'count')
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
            fields are all in the :class:`~genesisng.schema.login.Login` model
            class but the password.
        :type fields: str
        :param search: Search term (case insensitive). The passed term will be
            searched using pattern-matching indexes in the all fields.
        :type search: str

        :returns: A list of dicts with all attributes of a
            :class:`~genesisng.schema.login.Login` model class, minus the
            password.
        :rtype: list
        """

        # Shortcut to the entity columns
        cols = Login.__table__.columns

        # Database connection
        conn = self.user_config.genesisng.database.connection

        # Cache control default value
        cache_control = self.user_config.genesisng.cache.default_cache_control

        # Parse received arguments
        params = parse_args(self.request.input, self.allowed,
                            self.user_config.genesisng.pagination, self.logger)

        # Check whether a copy exists in the cache
        cache_key = 'page:%s|size:%s|criteria:%s|direction:%s|filters:%s|operator:%s|search:%s' % (
            params.page, params.size, params.criteria, params.direction,
            str(params.filters), params.operator, params.search)
        try:
            cache = self.cache.get_cache('builtin', 'logins')
        except Exception:
            self.logger.error("Could not get the 'logins' cache collection.")
        if cache is not None:
            cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.logger.info("Returning list of logins from the cache.")

            # Get a list of the fields to be removed
            diff = []
            if params.columns:
                diff += list(set(cache_data.value[0].keys()) -
                             set(params.columns))

            # Remove unwanted fields from the row
            payload = []
            for i in cache_data.value:
                d = {key: i[key] for key in i.keys() if key not in diff}
                payload.append(d)

            self.response.status_code = OK
            self.response.payload[:] = payload
            self.response.headers['Content-Language'] = 'en'
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = str(
                cache_data.last_write_http)
            self.response.headers['ETag'] = str(cache_data.hash)
            return

        # Compose query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))
            # Add columns to get a flat row of columns rather than entities
            for f in self.allowed.fields:
                query = query.add_columns(cols[f])

            # Prepare filters
            query = parse_filters(params.filters, params.operator, cols, query)

            # Search: add ilike clauses if there is a search term.
            if params.search:
                clauses = []
                for s in self.paging.search:
                    clauses.append(cols[s].ilike(params.search))
                query = query.filter(or_(*clauses))

            # Order by
            if params.direction == 'asc':
                query = query.order_by(cols[params.criteria].asc())
            else:
                query = query.order_by(cols[params.criteria].desc())

            # Add limit and offset
            query = query.offset(params.offset)
            query = query.limit(params.limit)

            # Execute query
            result = query.all()

            # Return now if no rows were returned
            if not result:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'
                return

            # Get a list of the fields to be removed
            diff = ['count']
            if params.columns:
                diff += list(set(result[0].keys()) - set(params.columns))

            # Empty list of dicts to be saved in the cache
            data = []

            # Empty list of dicts for the processed rows of the result set
            payload = []

            # Loop the result set
            for r in result:
                # Remove unwanted fields from the row
                d = {key: getattr(r._elem, key)
                     for key in r._elem.keys() if key not in diff}
                payload.append(d)

                # Convert each WritableKeyedTuple to a dict so that we store
                # a list of dicts in the cache
                d = {key: getattr(r._elem, key)
                     for key in r._elem.keys() if key not in ['count']}
                data.append(d)

                # Store each full row (as a dict) in the cache.
                # Passwords have already been excluded.
                if cache is not None:
                    cache.set('id:%s' % r.id, d)

            # Store the processed result set in the cache
            if cache is not None:
                self.logger.info("Storing list of logins in the cache.")
                cache_data = cache.set(cache_key, data, details=True)

            # Get the count from the last row
            params.count = r.count

            self.response.status_code = OK
            self.response.payload[:] = payload
            self.response.headers['Content-Language'] = 'en'
            self.response.headers['X-Genesis-Page'] = str(params.page)
            self.response.headers['X-Genesis-Size'] = str(params.size)
            self.response.headers['X-Genesis-Count'] = str(params.count)

            if cache_data:
                self.response.headers['Cache-Control'] = cache_control
                self.response.headers['Last-Modified'] = str(
                    cache_data.last_write_http)
                self.response.headers['ETag'] = str(cache_data.hash)
            else:
                self.response.headers['Cache-Control'] = 'no-cache'
