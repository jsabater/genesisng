# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from zato.server.service import Service, Integer, Float
from genesisng.schema.room import Room
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from urlparse import parse_qs


class Get(Service):
    """Service class to get a room by id."""
    """Channel /genesisng/rooms/get/{id}."""

    class SimpleIO:
        input_required = ('id')
        output_optional = ('id', 'floor_no', 'room_no', 'name', 'sgl_beds',
                           'dbl_beds', 'supplement', 'code', 'accommodates',
                           'number', 'deleted')

    def handle(self):
        conn = self.kvdb.conn.get('genesisng:database:connection')
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Room).\
                filter(and_(Room.id == id_, Room.deleted.is_(None))).\
                one_or_none()

            # FIXME: hybrid properties accommodates and number are not being
            # returned as part of the payload.
            if result:
                self.response.status_code = OK
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.payload = ''
