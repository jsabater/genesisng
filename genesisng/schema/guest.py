# coding: utf8
from genesisng.schema import Base
from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy import Index, Enum
from sqlalchemy.ext.hybrid import hybrid_property
import enum

# class Gender(str, enum.Enum):
#     Male: str = 'Male'
#     Female: str = 'Female'


class Gender(str, enum.Enum):
    Male = 1
    Female = 2


class Guest(Base):
    __tablename__ = 'guest'
    __rels__ = []
    __table_args__ = (
        # Trigram GIN indexes for searches (using ILIKE)
        Index('ix_trgm_guest_name', 'name', postgresql_using='gin',
              postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_surname', 'surname', postgresql_using='gin',
              postgresql_ops={'surname': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_email', 'email', postgresql_using='gin',
              postgresql_ops={'email': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_address1', 'address1', postgresql_using='gin',
              postgresql_ops={'address1': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_address2', 'address2', postgresql_using='gin',
              postgresql_ops={'address2': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_locality', 'locality', postgresql_using='gin',
              postgresql_ops={'locality': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_postcode', 'postcode', postgresql_using='gin',
              postgresql_ops={'postcode': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_province', 'province', postgresql_using='gin',
              postgresql_ops={'province': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_home_phone', 'home_phone', postgresql_using='gin',
              postgresql_ops={'home_phone': 'gin_trgm_ops'}),
        Index('ix_trgm_guest_mobile_phone', 'mobile_phone',
              postgresql_using='gin',
              postgresql_ops={'mobile_phone': 'gin_trgm_ops'}),
    )

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    # E-mail must be unique.
    # B-tree indexes on sorting fields to speed up operations and reduce memory
    # consumption.
    # https://www.postgresql.org/docs/current/static/indexes-ordering.html
    id = Column(Integer, primary_key=True)
    name = Column(String(50), index=True)
    surname = Column(String(50), index=True)
    gender = Column(Enum(Gender), index=True, default='Male')
    email = Column(String(255), index=True, unique=True)
    passport = Column(String(255))
    birthdate = Column(Date, index=True, default=None)
    address1 = Column(String(50))
    address2 = Column(String(50), default=None)
    locality = Column(String(50))
    postcode = Column(String(10))
    province = Column(String(50))
    country = Column(String(2), index=True)
    home_phone = Column(String(50), default=None)
    mobile_phone = Column(String(50), default=None)
    deleted = Column(DateTime, index=True, default=None)

    def __repr__(self):
        return "<Guest(id='%s', name='%s', surname='%s', email='%s')>" % (
            self.id, self.name, self.surname, self.email)

    @hybrid_property
    def fullname(self):
        return '%s %s' % (self.name, self.surname)
