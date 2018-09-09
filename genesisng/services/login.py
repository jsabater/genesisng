# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT, BAD_REQUEST
from zato.server.service import Service, Boolean, Integer
from genesisng.schema.login import Login
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from urlparse import parse_qs

class Get(Service):
    """Service class to get a login by id through channel /genesisng/logins/get/{id}."""

    class SimpleIO:
        input_required = ('id')
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).filter(Login.id == id_).one_or_none()

            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''

class Create(Service):
    """Service class to create a new login through channel /genesisng/logins/create."""

    class SimpleIO:
        input_required = ('username', 'password', 'name', 'surname', 'email')
        input_optional = (Boolean('is_admin'))
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.kvdb.conn.get('genesisng:database:connection')

        p = self.request.input
        l = Login(username=p.username, password=p.password, name=p.name, surname=p.surname, email=p.email)
        l.is_admin = p.get('is_admin', False)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(l)
                session.commit()
                self.response.status_code = CREATED
                self.response.payload = l
                url = self.kvdb.conn.get('genesisng:location:logins')
                self.response.headers['Location'] = '%s/%s' % (url, l.id)

            except IntegrityError as e:
                # Constraint prevents duplication of username or emails.
                session.rollback()
                self.response.status_code = CONFLICT
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948
                self.response.payload = ''

class Delete(Service):
    """Service class to delete an existing login through channel /genesisng/logins/delete/{id}"""

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')
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
    """Service class to update an existing login through channel /genesisng/logins/update/{id}"""

    class SimpleIO:
        input_required = ('id')
        input_optional = ('username', 'password', 'name', 'surname', 'email', 'is_admin')
        # XXX: Should output_required be output_optional given we can return NOT_FOUND?
        output_required = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')
        skip_empty_keys = True

    def handle(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')
        id_ = self.request.input.id
        p = self.request.input
        l = Login(id=id_, username=p.username, password=p.password, name=p.name, surname=p.surname, email=p.email, is_admin=p.is_admin)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).filter(Login.id == id_).one_or_none()

            if result:
                # Update dictionary keys
                result.username = l.username
                result.password = l.password
                result.name = l.name
                result.surname = l.surname
                result.email = l.email
                result.is_admin = l.is_admin
                session.commit()
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''

class List(Service):
    """Service class to get a list of all logins in the system through channel /genesisng/logins/list."""

    class SimpleIO:
        input_optional = ('page', 'size', 'sort_by', 'order_by', 'filters', 'search', 'fields')
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')
        output_repeated = True
        skip_empty_keys = True

    def handle(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')
        default_page_size = int(self.kvdb.conn.get('genesisng:database:default_page_size'))
        max_page_size = int(self.kvdb.conn.get('genesisng:database:max_page_size'))
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
                # Fields allowed for ordering are id, username, name, surname and email
                if order_by not in ('id', 'username', 'name', 'surname', 'email'):
                    order_by = default_order_by

                sort_by = qs['sort_by'][0].lower()
                sort_by = default_sort_by if sort_by not in ('asc', 'desc') else sort_by
            except (ValueError, KeyError, IndexError):
                # Assume default values instead of returning 400 Bad Request
                pass

            # Handle filtering
            try:
                for f in qs['filters']:
                    field, operator, value = f.split('|')
                    if field not in ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin'):
                        raise ValueError('Field %s is not allowed for filtering' % field)
                    if operator not in ('lt', 'lte', 'eq', 'ne', 'gte', 'gt'):
                        raise ValueError('Operator %s is not allowed for filtering' % operator)
                    filters.append((field, operator, value))
            except (ValueError, KeyError):
                # Do not apply any filtering instead of returning 400 Bad Request
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
                    if field not in ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin'):
                        raise ValueError('Field %s is not allowed for projection' % field)
                    fields.append(field)
            except (ValueError, KeyError):
                # Do not apply any fields projection instead of returning 400 Bad Request
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
            fields = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')
        columns = [Login.__table__.columns[field] for field in fields]

        # Execute query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))
            for c in columns:
                query = query.add_columns(c)
            for c in conditions:
                query = query.filter(c)
            if search:
                query = query.filter(or_(
                    Login.username.ilike(term),
                    Login.name.ilike(term),
                    Login.surname.ilike(term),
                    Login.email.ilike(term)
                ))
            if direction == 'asc':
                query = query.order_by(Login.__table__.columns[criteria].asc())
            else:
                query = query.order_by(Login.__table__.columns[criteria].desc())
            query = query.offset(offset)
            query = query.limit(limit)
            result = query.all()
            self.response.payload[:] = result if result else []
