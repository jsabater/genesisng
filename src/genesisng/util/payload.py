# -*- coding: utf-8 -*-
from bunch import Bunch


class Payload(Bunch):
    """Defines the skeleton of a payload to be returned by a service."""

    def __init__(self, page=None, size=None, count=None, data=None):
        self.data = data
        self.meta = None
        self.pagination = Bunch({
            'page': page,
            'size': size,
            'count': count
        })
        self.error = Bunch({
            'code': None,
            'message': None
        })

    def set_error(self, code=None, message=None):
        self.error.code = code
        self.error.message = message
