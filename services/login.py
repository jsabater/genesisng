# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED
from zato.server.service import Service
from genesisng.schema.login import Login

class Get(Service):
    """Service class to get a login by id through channel /genesisng/logins/get/{id}."""

    class SimpleIO:
        input_required = ('id')
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        """Returns a login given its id."""

        conn = self.kvdb.conn.get('genesisng:database:connection')
        id_ = self.request.input.id
        self.logger.info('Checking for a login with id: %s' % id_)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).filter(Login.id == id_).one_or_none()

            if result:
                self.logger.info('Retrieved login: {}' . format(result))
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.logger.info('Could not find a login with id: %s' % id_)
                self.response.status_code = NO_CONTENT

class List(Service):
    """Service class to get a list of all logins in the system through channel /genesisng/logins/list."""

    class SimpleIO:
        input_required = ()
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        """Returns a list of all logins in the system."""

        conn = self.kvdb.conn.get('genesisng:database:connection')
        self.logger.info('Getting a list of customers.')

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Login).order_by(Login.id)
            output = []
            for row in result:
                output.append(row)
            self.logger.info(output)
            self.response.payload[:] = output

class Create(Service):
    """Service class to create a new login through channel /genesisng/logins/create."""

    class SimpleIO:
        input_required = ('username', 'password', 'name', 'surname', 'email', 'is_admin')
        output_required = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        """Creates a new login. All attributes are mandatory. Returns location header."""
        conn = self.kvdb.conn.get('genesisng:database:connection')
        
        # Create a Login instance and populate it with input parameters
        params = self.request.input
        login = Login(username=params.username, password=params.password, name=params.name, surname=params.surname, email=params.email, is_admin=params.is_admin)

        self.logger.info('Creating a login: {}' . format(params))

        with closing(self.outgoing.sql.get(conn).session()) as session:
            session.add(login)
            session.commit()

            self.response.status_code = CREATED
            self.response.payload = login
            url = self.kvdb.conn.get('genesisng:location:logins')
            self.response.headers['Location'] = '%s/%s' % (url, login.id)
