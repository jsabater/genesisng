# -*- coding: utf-8 -*-
from bunch import Bunch


class Payload(Bunch):
    """Defines the skeleton of a payload to be returned by a service."""
    data = None
    meta = None
    pagination = None
    error = None

    def __init__(self):
        data = {}
        meta = {}
        pagination = {
            'page': None,
            'size': None,
            'count': None
        }
        error = {
            'code': None,
            'message': None
        }
        self.data = data
        self.meta = meta
        self.pagination = pagination
        self.error = error
