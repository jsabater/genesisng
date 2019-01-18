# coding: utf8
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from .base import Base
from sqlalchemy import Column, Boolean, Integer, String, Index, func
from sqlalchemy.orm import deferred
from sqlalchemy.ext.hybrid import hybrid_property, Comparator
from passlib.hash import bcrypt


class PasswordComparator(Comparator):
    """Comparator class used to hash the clear-text password sent to the
    database and verify it against the stored value."""
    def __eq__(self, other):
        return self.__clause_element__() == \
            func.crypt(other, self.__clause_element__())


class Login(Base):
    """
    Model class to represent a login in the system.

    Includes trigram GIN indexes for pattern-matching searches on fields
    `username`, `name` and `surname` and b-tree indexes to compare, sort and
    reduce memory consumption on fields `username`, `name`, `surname` and
    `email`.

    Uses the BCrypt algorithm from the `passlib`_ library (which also uses
    `bcrypt`_) to hash passwords. When adding new records, passwords are hashed
    before being sent to the database. When validating, a custom comparator is
    used to send passwords to the database, which uses its cryptographic
    functions to verify it.

    .. _passlib: https://pypi.org/project/passlib/
    .. _bcrypt: https://pypi.org/project/bcrypt/
    """

    __tablename__ = 'login'
    __rels__ = []
    __table_args__ = (
        # Trigram GIN indexes for searches (using ILIKE)
        Index('ix_trgm_login_username', 'username', postgresql_using='gin',
              postgresql_ops={'username': 'gin_trgm_ops'}),
        Index('ix_trgm_login_name', 'name', postgresql_using='gin',
              postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('ix_trgm_login_surname', 'surname', postgresql_using='gin',
              postgresql_ops={'surname': 'gin_trgm_ops'}),
    )

    id = Column(Integer, primary_key=True)
    """Primary key. Autoincrementing integer."""
    username = Column(String(20), index=True, unique=True, nullable=False)
    """Username or alias of the person. Must be unique."""
    _password = deferred(Column('password', String(255), nullable=False))
    name = Column(String(50), index=True)
    """First name of the person."""
    surname = Column(String(50), index=True)
    """Last name of the person."""
    email = Column(String(255), index=True, unique=True)
    """Electronic mail address. Must be unique."""
    is_admin = Column(Boolean, default=False)
    """Is this person an administrator?"""

    @hybrid_property
    def password(self):
        """Hashed password. Uses `deferred()`_ to prevent the field from being
        fetched by default when an object is loaded from the database.

        .. _deferred(): https://docs.sqlalchemy.org/en/latest/orm/loading_columns.html
        """
        return self._password

    @password.comparator
    def password(cls):
        return PasswordComparator(cls._password)

    @password.setter
    def password(self, plaintext_password):
        self._password = bcrypt.hash(plaintext_password)

    def __repr__(self):
        """String representation of the object."""
        return "<Login(id='%s', username='%s', name='%s', surname='%s', email='%s')>" % (
            self.id, self.username, self.name, self.surname, self.email)
