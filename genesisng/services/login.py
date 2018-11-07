# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service, Boolean, Integer, AsIs, List
from genesisng.schema.login import Login
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from hashlib import md5


class Get(Service):
    """Service class to get a login by id."""
    """Channel /genesisng/logins/{id}/get."""

    class SimpleIO:
        input_required = (Integer('id'))
        # Passwords never travel back to the client side
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        id_ = self.request.input.id

        # Check whether a copy exists in the cache
        cache_key = 'id-%s' % id_
        cache = self.cache.get_cache('builtin', 'logins')
        cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = format_date_time(
                cache_data.last_write)
            self.response.headers['ETag'] = md5(str(
                cache_data.value)).hexdigest()
            self.response.payload = cache_data.value
            return

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).filter(Login.id == id_).one_or_none()

            if result:
                # Save the record in the cache, minus the password
                result = result.asdict()
                del (result['password'])
                cache.set(cache_key, result)
                self.response.status_code = OK
                self.response.headers['Cache-Control'] = cache_control
                self.response.headers['Last-Modified'] = format_date_time(
                    mktime(datetime.now().timetuple()))
                self.response.headers['ETag'] = md5(str(result)).hexdigest()
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Validate(Service):
    """Service class to validate credentials."""
    """Channel /genesisng/logins/validate."""

    class SimpleIO:
        input_required = ('username', AsIs('password'))
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        username = self.request.input.username
        password = self.request.input.password

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).\
                filter(and_(Login.username == username,
                            Login.password == password)).\
                one_or_none()

            if result:
                # Save the record in the cache, minus the password
                cache_key = 'id-%s' % result.id
                cache = self.cache.get_cache('builtin', 'logins')
                result = result.asdict()
                del (result['password'])
                cache.set(cache_key, result)
                self.response.status_code = OK
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Create(Service):
    """Service class to create a new login."""
    """Channel /genesisng/logins/create."""

    class SimpleIO:
        input_required = ('username', AsIs('password'))
        input_optional = ('name', 'surname', 'email',
                          Boolean('is_admin', default=False))
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        skip_empty_keys = True

    def handle(self):
        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        result = Login(
            username=p.username,
            password=p.password,
            name=p.name,
            surname=p.surname,
            email=p.email,
            is_admin=p.is_admin)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(result)
                session.commit()

                # Save the record in the cache, minus the password
                cache_key = 'id-%s' % result.id
                cache = self.cache.get_cache('builtin', 'logins')
                result = result.asdict()
                del (result['password'])
                cache.set(cache_key, result)

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
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class Delete(Service):
    """Service class to delete an existing login."""
    """Channel /genesisng/logins/{id}/delete."""

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            deleted = session.query(Login).filter(Login.id == id_).delete()
            session.commit()

            if deleted:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'

                # Invalidate the cache
                cache_key = 'id-%s' % id_
                cache = self.cache.get_cache('builtin', 'logins')
                cache.delete(cache_key)

            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Update(Service):
    """Service class to update an existing login."""
    """Channel /genesisng/logins/{id}/update."""

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = ('username', AsIs('password'), 'name', 'surname',
                          'email', Boolean('is_admin'))
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                result = session.query(Login).filter(Login.id == id_).\
                         one_or_none()

                if result:
                    # TODO: Implement a wrapper to remove empty request keys,
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
                    cache_key = 'id-%s' % result.id
                    cache = self.cache.get_cache('builtin', 'logins')
                    result = result.asdict()
                    del (result['password'])
                    cache.set(cache_key, result)

                    # Return the result
                    self.response.status_code = OK
                    self.response.payload = result
                    self.response.headers['Cache-Control'] = 'no-cache'

                    # Invalidate the cache
                    cache_key = 'id-%s' % id_
                    cache = self.cache.get_cache('builtin', 'logins')
                    cache.delete(cache_key)
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
    """Service class to get a list of all logins in the system."""
    """Channel /genesisng/logins/list."""

    model = Login
    criteria_allowed = ('id', 'username', 'name', 'surname', 'email')
    direction_allowed = ('asc', 'desc')
    filters_allowed = ('id', 'username', 'name', 'surname', 'email',
                       'is_admin')
    comparisons_allowed = ('lt', 'lte', 'eq', 'ne', 'gte', 'gt')
    operators_allowed = ('and', 'or')
    fields_allowed = ('id', 'username', 'name', 'surname', 'email', 'is_admin')
    search_allowed = ('username', 'name', 'surname', 'email')

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('fields'), List('operator'),
                          List('search'))
        output_required = ('count')
        output_optional = ('id', 'username', 'name', 'surname', 'email',
                           'is_admin')
        output_repeated = True
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        default_page_size = int(
            self.user_config.genesisng.pagination.default_page_size)
        max_page_size = int(
            self.user_config.genesisng.pagination.max_page_size)
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
                # Store results in the cache only if all fields were retrieved
                if not fields:
                    cache = self.cache.get_cache('builtin', 'logins')
                    for r in result:
                        cache_key = 'id-%s' % r.id
                        r = r.asdict()
                        del (r['password'])
                        cache.set(cache_key, r)

                self.response.status_code = OK
                self.response.payload[:] = result
                self.response.headers['Cache-Control'] = 'no-cache'
            else:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'
