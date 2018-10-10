# coding: utf8
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from .base import Base
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
import hashids


def generate_code(context):
    # TODO: Add a salt value?
    # hashids = Hashids(salt='this is my salt 1')
    # hashid = hashids.encode(value)
    return hashids.encode(context.current_parameters.get('floor_no'),
                          context.current_parameters.get('room_no'),
                          context.current_parameters.get('sgl_beds'),
                          context.current_parameters.get('dbl_beds'))


class Room(Base):
    __tablename__ = 'room'
    __rels__ = []
    __table_args__ = (
        # Combination of floor number and room number must be unique.
        UniqueConstraint('floor_no', 'room_no', name='room_floor_no_room_no'),
        # The sum of beds must be a positive integer.
        CheckConstraint('sgl_beds + dbl_beds > 0'),
    )

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    id = Column(Integer, primary_key=True)
    floor_no = Column(Integer, nullable=False)
    room_no = Column(Integer, nullable=False)
    name = Column(String(100), index=True)
    sgl_beds = Column(Integer, nullable=False, default=0, index=True)
    dbl_beds = Column(Integer, nullable=False, default=0, index=True)
    supplement = Column(Float, nullable=False, default=0)
    code = Column(
        String(32),
        nullable=False,
        default=generate_code,
        unique=True,
        comment='Unique code used to link to images')
    deleted = Column(DateTime, default=None)

    def __repr__(self):
        return "<Room(id='%s', number='%s', accommodates='%s')>" % (
            self.id, self.number, self.accommodates)

    @hybrid_property
    def accommodates(self):
        return self.sgl_beds + self.dbl_beds * 2

    @hybrid_property
    def number(self):
        return '%d%02d' % (self.floor_no, self.room_no)
