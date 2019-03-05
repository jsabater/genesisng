# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from zato.server.service import Service


class Sender(Service):
    def handle(self):
        self.logger.info('Executing sender subscriber service')
        topic_name = '/genesisng/bookings/new'
        sub_key = self.pubsub.subscribe(topic_name, service=self)
        self.logger.info('Sender service subscribed to topic name %s and received subscription key %s',
                         topic_name, sub_key)

        # Get available messages
        messages = self.pubsub.get_messages(topic_name, sub_key)
        self.logger.info('Messages received from topic name %s are %s',
                         topic_name, messages)

        # Compose a new reservation email and send it to the guest
        self.logger.info('Sending email to guest')
