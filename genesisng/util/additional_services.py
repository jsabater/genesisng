# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from bunch import Bunch


class AdditionalServices(Bunch):
    """Defines the additional services available for bookings."""
    items = None

    def __init__(self):
        default = {
            'LateDinner': 'Late dinner',
            'PoolKit': 'Pool kit',
            'Massage30': '30 minutes massage'
        }
        self.items = Bunch(default)
