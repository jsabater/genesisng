# coding: utf8

from contextlib import closing
from zato.server.service import Service
from genesis-ng.schema.login import Login

class GetLogin(Service):

    #class SimpleIO(object):
    #    output_required = ('username', 'password', 'name', 'surname', 'email', 'is_admin')

    def handle(self):

        out_name = 'Genesis'
        username = 'jsabater@gmail.com'

        with closing(self.outgoing.sql.get(out_name).session()) as session:
            login = session.query(Login).\
                    filter(Login.email==username).\
                    one()

            self.response.payload = login
            # self.logger.info(login)

