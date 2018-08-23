# coding: utf8
from schema import Base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM

class Gender(ENUM):
    name = 'Gender'
    male = 'Male'
    female = 'Female'

class Guest(Base):
    __tablename__ = 'guest'
    __rels__ = []
    __table_args__ = (
        UniqueConstraint('email', name='guest_email'),
    )

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    surname = Column(String(50))
    gender = Column(ENUM(Gender), default='Male')
    email = Column(String(255))
    passport = Column(String(255))
    birthdate = Column(Date)
    address1 = Column(String(50))
    address2 = Column(String(50))
    locality = Column(String(50))
    postcode = Column(String(10))
    province = Column(String(50))
    country = Column(String(2))
    home_phone = Column(String(50))
    mobile_phone = Column(String(50))
    deleted = Column(Date, default=None)

    def __repr__(self):
        return "<Guest(name='%s', surname='%s', email='%s')>" % (
            self.name, self.surname, self.email)

