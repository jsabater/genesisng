# coding: utf8
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from .base import Base
from sqlalchemy import Column, Integer, Float, String, DateTime


class Extra(Base):
    """
    Model class to represent an extra in the system.

    Records are not deleted from the database but instead marked as deleted
    via the :attr:`~genesisng.schema.extra.Extra.deleted` attribute, which
    contains a timestamp of the date and time when the record was deleted.
    """

    __tablename__ = 'extra'
    __rels__ = []
    __table_args__ = ()

    id = Column(Integer, primary_key=True)
    """Primary key. Autoincrementing integer."""
    code = Column(String(15), index=True, nullable=False)
    """An internal code to be used when storing the data as a dictionary."""
    name = Column(String(50), nullable=False)
    """The name of the extra."""
    description = Column(String(255), nullable=False)
    """The description of the extra."""
    price = Column(Float, nullable=False, default=0)
    """The price of the extra. Price per service."""
    deleted = Column(DateTime, index=True, default=None)
    """Timestamp of the deletion of the record. Defaults to None."""

    def __repr__(self):
        """String representation of the object."""
        return "<Extra(id='%s', code='%s', name='%s', price='%s')>" % (
            self.id, self.code, self.name, self.price)
