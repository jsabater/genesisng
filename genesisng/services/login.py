# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service, Boolean, Integer, AsIs
from genesisng.schema.login import Login
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from urlparse import parse_qs


class Get(Service):
    """Service class to get a login by id."""
    """Channel /genesisng/logins/{id}/get."""

    class SimpleIO:
        input_required = (Integer('id'),)
        output_required = ('id', 'username')
        output_optional = ('password', 'name', 'surname', 'email', 'is_admin')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).filter(Login.id == id_).one_or_none()

            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class Validate(Service):
    """Service class to validate credentials."""
    """Channel /genesisng/logins/validate."""

    class SimpleIO:
        input_required = ('username', AsIs('password'))
        output_required = ('id', 'username')
        output_optional = ('password', 'name', 'surname', 'email', 'is_admin')
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
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class Create(Service):
    """Service class to create a new login."""
    """Channel /genesisng/logins/create."""

    class SimpleIO:
        input_required = ('username', AsIs('password'))
        input_optional = ('name', 'surname', 'email',
                          Boolean('is_admin', default=False))
        output_required = ('id', 'username')
        output_optional = ('password', 'name', 'surname', 'email', 'is_admin')
        skip_empty_keys = True

    def handle(self):
        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        login = Login(
            username=p.username,
            password=p.password,
            name=p.name,
            surname=p.surname,
            email=p.email,
            is_admin=p.is_admin)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(login)
                session.commit()
                self.response.status_code = CREATED
                self.response.payload = login
                url = self.user_config.genesisng.location.logins
                self.response.headers['Location'] = url.format(id=login.id)

            except IntegrityError:
                # Constraint prevents duplication of username or emails.
                session.rollback()
                self.response.status_code = CONFLICT
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948
                self.response.payload = ''


class Delete(Service):
    """Service class to delete an existing login."""
    """Channel /genesisng/logins/{id}/delete."""

    class SimpleIO:
        input_required = (Integer('id'),)

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            deleted = session.query(Login).filter(Login.id == id_).delete()
            session.commit()

            if deleted:
                self.response.status_code = NO_CONTENT
                self.response.payload = ''
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class Update(Service):
    """Service class to update an existing login."""
    """Channel /genesisng/logins/{id}/update."""

    class SimpleIO:
        input_required = (Integer('id'),)
        input_optional = ('username', AsIs('password'), 'name', 'surname',
                          'email', Boolean('is_admin'))
        output_required = ('id', 'username')
        output_optional = ('password', 'name', 'surname', 'email', 'is_admin')
        skip_empty_keys = True

    def handle(self):
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).filter(Login.id == id_).one_or_none()

            if result:
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
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''


class List(Service):
    """Service class to get a list of all logins in the system."""
    """Channel /genesisng/logins/list."""

    class SimpleIO:
        input_optional = (Integer('page'), Integer('size'), 'sort_by',
                          'order_by', 'filters', 'search', 'fields')
        output_required = ('count', )
        output_optional = ('id', 'username', 'password', 'name', 'surname',
                           'email', 'is_admin')
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
                # Fields allowed for ordering are id, username, name, surname
                # and email
                if order_by not in ('id', 'username', 'name', 'surname',
                                    'email'):
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
                    if field not in ('id', 'username', 'password', 'name',
                                     'surname', 'email', 'is_admin'):
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
                    if field not in ('id', 'username', 'password', 'name',
                                     'surname', 'email', 'is_admin'):
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
                conditions.append(Login.__table__.columns[field] < value)
            elif operator == 'lte':
                conditions.append(Login.__table__.columns[field] <= value)
            elif operator == 'eq':
                conditions.append(Login.__table__.columns[field] == value)
            elif operator == 'ne':
                conditions.append(Login.__table__.columns[field] != value)
            elif operator == 'gte':
                conditions.append(Login.__table__.columns[field] >= value)
            elif operator == 'gt':
                conditions.append(Login.__table__.columns[field] > value)

        # Prepare search
        if search:
            term = '%' + search + '%'

        # Prepare fields projection
        columns = []
        if not fields:
            fields = ('id', 'username', 'password', 'name', 'surname', 'email',
                      'is_admin')
        columns = [Login.__table__.columns[f] for f in fields]

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
                        Login.username.ilike(term), Login.name.ilike(term),
                        Login.surname.ilike(term), Login.email.ilike(term)))
            if direction == 'asc':
                query = query.order_by(Login.__table__.columns[criteria].asc())
            else:
                query = query.order_by(
                    Login.__table__.columns[criteria].desc())
            query = query.offset(offset)
            query = query.limit(limit)
            result = query.all()
            self.response.payload[:] = result if result else []
