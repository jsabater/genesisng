# coding: utf8
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from sqlalchemy.ext.declarative import declarative_base
from dictalchemy import DictableModel


Base = declarative_base(cls=DictableModel)
