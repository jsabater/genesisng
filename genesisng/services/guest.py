# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED
from zato.server.service import Service
from genesisng.schema import guest
# from urlparse import parse_qs

class Guest(Service):

    class SimpleIO(object):
        input_optional = ('id', 'name', 'surname', 'gender', 'email', 'passport',
            'birthdate', 'address1', 'address2', 'locality', 'postcode', 'province',
            'country', 'home_phone', 'mobile_phone')
        output_optional = ('id', 'name', 'surname', 'gender', 'email', 'passport',
            'birthdate', 'address1', 'address2', 'locality', 'postcode', 'province',
            'country', 'home_phone', 'mobile_phone')

    def handle_GET(self):
        # qs = parse_qs(self.wsgi_environ[‘QUERY_STRING’])
        # self.logger.info(qs['foo'])

        conn = self.kvdb.conn.get('genesisng:database:connection')
        id_ = self.request.input.id
        self.logger.info('Checking for a guest with id: %s' % id_)

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(guest.Guest).filter(guest.Guest.id == id_).one_or_none()

            if result:
                self.logger.info('Retrieved guest: {}' . format(result))
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.logger.info('Could not find a guest with id: %s' % id_)
                self.response.status_code = NO_CONTENT

    def handle_POST(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')
        
        # Create a Guest instance and populate it with input parameters
        params = self.request.input
        new_guest = guest.Guest(name=params.name, surname=params.surname, gender=params.gender,
            email=params.email, passport=params.passport, birthdate=params.birthdate,
            address1=params.address1, address2=params.address2, locality=params.locality,
            postcode=params.postcode, province=params.province, country=params.country,
            home_phone=params.home_phone, mobile_phone=params.mobile_phone)

        self.logger.info('Creating a guest: {}' . format(params))

        with closing(self.outgoing.sql.get(conn).session()) as session:
            session.add(new_guest)
            session.commit()

            self.response.status_code = CREATED
            self.response.payload = new_guest
            url = self.kvdb.conn.get('genesisng:location:guests')
            self.response.headers['Location'] = '%s/%s' % (url, new_guest.id)

# class List(Service):

#     class SimpleIO(object):
#         input_required = ()
#         output_required = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

#     def handle(self):
#         conn = self.kvdb.conn.get('genesisng:database:connection')
#         self.logger.info('Getting a list of customers.')

#         with closing(self.outgoing.sql.get(conn).session()) as session:
#             result = session.query(Login).all()

#             self.response.payload = result
