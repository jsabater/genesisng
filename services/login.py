# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED
from zato.server.service import Service
from genesisng.schema.login import Login

class GetLogin(Service):

    class SimpleIO(object):
        input_required = ('id')
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        out_name = self.kvdb.conn.get('genesisng:database:connection')
        id = self.request.input.id
        self.logger.info('Checking for a login with id: %s' % id)

        with closing(self.outgoing.sql.get(out_name).session()) as session:
            result = session.query(Login).filter(Login.id == id).one_or_none()

            if result:
                self.logger.info('Retrieved login: {}' . format(result))
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.logger.info('Could not find a login with id: %s' % id)
                self.response.status_code = NO_CONTENT

class NewLogin(Service):

    class SimpleIO(object):
        input_required = ('username', 'password', 'name', 'surname', 'email')
        input_optional = ('is_admin')
        output_required = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        out_name = self.kvdb.conn.get('genesisng:database:connection')
        
        # Create a Login instance and populate it with input parameters
        i = self.request.input
        l = Login(username=i.username, password=i.password, name=i.name, surname=i.surname, email=i.email)
        # l.is_admin = i.get('is_admin')

        self.logger.info('Creating a login: {}' . format(i))

        with closing(self.outgoing.sql.get(out_name).session()) as session:
            session.add(l)
            session.commit()

            self.response.status_code = CREATED
            self.response.payload = l
            url = self.kvdb.conn.get('genesisng:location:logins')
            self.response.headers['Location'] = '%s/%s' % (url, l.id)
