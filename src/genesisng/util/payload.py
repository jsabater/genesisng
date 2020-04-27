# -*- coding: utf-8 -*-
from bunch import Bunch


class Payload(object):
    """Defines the skeleton of a payload to be returned by a service."""
    data = None
    meta = None
    pagination = None
    error = None

    def __init__(self, page=None, size=None, count=None):
        self.data = {}
        self.meta = {}
        self.pagination = Bunch({
            'page': page,
            'size': size,
            'count': count
        })
        self.error = Bunch({
            'code': None,
            'message': None
        })
