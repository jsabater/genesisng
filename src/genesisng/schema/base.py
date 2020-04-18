# coding: utf8
from sqlalchemy.ext.declarative import declarative_base
from dictalchemy import DictableModel


Base = declarative_base(cls=DictableModel)
