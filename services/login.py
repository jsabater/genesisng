# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service
from genesisng.schema.login import Login
from sqlalchemy.exc import IntegrityError

class Get(Service):
    """Service class to get a login by id through channel /genesisng/logins/get/{id}."""

    class SimpleIO:
        input_required = ('id')
        # Cannot use output_required because Zato throws an exception when we return NOT_FOUND
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

class List(Service):
    """Service class to get a list of all logins in the system through channel /genesisng/logins/list."""

    class SimpleIO:
        input_required = ()
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')
        output_repeat = True

    def handle(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).order_by(Login.id)
            self.response.payload[:] = result if result else []

class Create(Service):
    """Service class to create a new login through channel /genesisng/logins/create."""

    class SimpleIO:
        input_required = ('username', 'password', 'name', 'surname', 'email')
        input_optional = ('is_admin')
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')
        p = self.request.input
        l = Login(username=p.username, password=p.password, name=p.name, surname=p.surname, email=p.email)
        l.is_admin = p.get('is_admin', False)
        # l.is_admin = p.get('is_admin', False) in ('True', 'true')

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
                self.response.payload = ''

class Delete(Service):
    """Service class to delete an existing login through channel /genesisng/logins/delete/{id}"""

    class SimpleIO:
        input_required = ('id')

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
        output_required = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

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
