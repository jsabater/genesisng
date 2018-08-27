# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import closing
from httplib import NO_CONTENT
from zato.server.service import Service
from sqlalchemy import or_
from genesisng.schema.login import Login

class LoginService(Service):

    class SimpleIO(object):
        input_required = ('username')
        output_optional = ('id', 'username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle_GET(self):
        # TODO: Add this to a configuration file an use the value
        # https://zato.io/docs/progguide/service-local-config.html
        out_name = 'Genesis'
        u = self.request.input.username
        self.logger.info('Checking for a login with username: %s' % u)

        with closing(self.outgoing.sql.get(out_name).session()) as session:
            result = session.query(Login).filter(or_(Login.username == u, Login.email == u)).one_or_none()

            if result:
                self.logger.info('Retrieved login: {}' . format(result))
                self.response.payload = result
            else:
                self.logger.info('Could not find a login with username: %s' % u)
                self.response.status_code = NO_CONTENT
