# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from bunch import Bunch


class Payload(Bunch):
    """Defines the skeleton of a payload to be returned by a service."""
    payload = None

    def __init__(self):
        default = {
            'data': {},
            'meta': {
                'page': None,
                'size': None,
                'count': None
            },
            'error': {
                'code': None,
                'message': None
            }
        }
        self.payload = Bunch(default)
