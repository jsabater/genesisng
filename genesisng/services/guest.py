# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT, BAD_REQUEST
from zato.server.service import Service, Boolean, Integer
from genesisng.schema.guest import Guest
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from urlparse import parse_qs

class Get(Service):
    """Service class to get a guest by id through channel /genesisng/guests/get/{id}."""

    class SimpleIO(object):
        input_required = ('id')
        output_optional = ('id', 'name', 'surname', 'gender', 'email', 'passport',
            'birthdate', 'address1', 'address2', 'locality', 'postcode', 'province',
            'country', 'home_phone', 'mobile_phone', 'deleted')

    def handle(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Guest).filter(and_(Guest.id == id_, Guest.deleted == None)).one_or_none()

            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''
