# coding: utf8
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from .base import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Index
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Enum as sqlEnum
from enum import Enum as pyEnum


class Gender(str, pyEnum):
    """
    Enumeration to support the gender.

    Possibles values are ``Male`` and ``Female``.

    Additionally, it also inherits from ``str`` to make JSON serialization
    possible.
    """

    Male = 1
    Female = 2


class Guest(Base):
    """
    Model class to represent a guest in  the system.

    Includes trigram GIN indexes for pattern-matching searches on fields
    `name`, `surname`, `email`, `address1`, `address2`, `locality`, `postcode`,
    `province`, `home_phone` and `mobile_phone` and b-tree indexes to
    compare, sort and reduce memory consumption on fields `name`, `surname`,
    `gender`, `email`, `birthdate`, `country` and `deleted`.

    Records are not deleted from the database but instead marked as deleted
    via the :attr:`~genesisng.schema.guest.Guest.deleted` attribute, which
    contains a timestamp of the date and time when the record was deleted.
    """

    __tablename__ = 'guest'
    __rels__ = []
    __table_args__ = (
        # Trigram GIST indexes for searches (using ILIKE)
        Index('ix_trgm_guest_name', 'name', postgresql_using='gist',
              postgresql_ops={'name': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_surname', 'surname', postgresql_using='gist',
              postgresql_ops={'surname': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_email', 'email', postgresql_using='gist',
              postgresql_ops={'email': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_address1', 'address1', postgresql_using='gist',
              postgresql_ops={'address1': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_address2', 'address2', postgresql_using='gist',
              postgresql_ops={'address2': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_locality', 'locality', postgresql_using='gist',
              postgresql_ops={'locality': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_postcode', 'postcode', postgresql_using='gist',
              postgresql_ops={'postcode': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_province', 'province', postgresql_using='gist',
              postgresql_ops={'province': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_home_phone', 'home_phone',
              postgresql_using='gist',
              postgresql_ops={'home_phone': 'gist_trgm_ops'}),
        Index('ix_trgm_guest_mobile_phone', 'mobile_phone',
              postgresql_using='gist',
              postgresql_ops={'mobile_phone': 'gist_trgm_ops'}),
    )

    id = Column(Integer, primary_key=True)
    """Primary key. Autoincrementing integer."""
    name = Column(String(50), index=True, nullable=False)
    """First name of the person."""
    surname = Column(String(50), index=True, nullable=False)
    """Last name of the person."""
    gender = Column(sqlEnum(Gender), index=True, default='Male')
    """Gender of the person. Defaults to Male."""
    email = Column(String(255), index=True, unique=True, nullable=False)
    """Electronic mail address. Must be unique."""
    passport = Column(String(255))
    """Passport number, tax id or similar identification number."""
    birthdate = Column(Date, index=True, default=None)
    """Date of birth of the person. Defaults to None."""
    address1 = Column(String(50))
    """Postal address."""
    address2 = Column(String(50), default=None)
    """Postal address. Additional information. Defaults to None."""
    locality = Column(String(50))
    """The city, town or similar."""
    postcode = Column(String(10))
    """Postal code."""
    province = Column(String(50))
    """Province, county, state or similar."""
    country = Column(String(2), index=True)
    """ISO 3166-1 alpha-2 code of the country."""
    home_phone = Column(String(50), default=None)
    """Home phone number using international format (e.g. +34.0123456789).
    Defaults to None."""
    mobile_phone = Column(String(50), default=None)
    """Mobile phone number using international format (e.g. +34.0123456789).
    Defaults to None."""
    deleted = Column(DateTime, index=True, default=None)
    """Timestamp of the deletion of the record. Defaults to None."""

    def __repr__(self):
        """String representation of the object."""
        return "<Guest(id='%s', name='%s', surname='%s', email='%s')>" % (
            self.id, self.name, self.surname, self.email)

    @hybrid_property
    def fullname(self):
        """Full name of the person. Since both name and surname cannot be
        empty, it is just the concatenation of such two strings."""
        return '%s %s' % (self.name, self.surname)
