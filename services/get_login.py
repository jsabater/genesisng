# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import closing
from zato.server.service import Service
# from genesisng import *

class GetLogin(Service):

    #class SimpleIO(object):
    #    output_required = ('username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):
        self.logger.info('You just got your login. YAY!')

        #out_name = 'Genesis'
        #username = 'jsabater@gmail.com'

        #with closing(self.outgoing.sql.get(out_name).session()) as session:
        #    result = session.query(login.Login).\
        #            filter(login.Login.email==username).\
        #            one()

        #    self.response.payload = result
