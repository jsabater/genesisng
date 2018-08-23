# coding: utf8
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from schema import login
from schema import guest
from schema import room
from schema import rate
from schema import booking

__all__ = ['login', 'guest', 'room', 'rate', 'booking']

