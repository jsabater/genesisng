# coding: utf8
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import enum
from uuid import uuid4
from .base import Base
from sqlalchemy import Column, Integer, Float, String, Date, DateTime
from sqlalchemy import func, text
from sqlalchemy import UniqueConstraint, CheckConstraint, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
# from sqlalchemy.orm import relationship


class BookingStatus(str, enum.Enum):
    New = 1
    Pending = 2
    Confirmed = 3
    Cancelled = 4
    Closed = 5


class BookingMealPlan(str, enum.Enum):
    RoomOnly = 1
    BedAndBreakfast = 2
    HalfBoard = 3
    FullBoard = 4
    AllInclusive = 5
    Special = 6


class Booking(Base):
    __tablename__ = 'booking'
    __rels__ = []
    __table_args__ = (
        # FIXME: Prevent overlappings using dates as well
        UniqueConstraint('id_guest', 'id_room', 'check_in',
                         name='booking_id_guest_id_room_check_in'),
        # Never check out before checking in
        CheckConstraint('check_in < check_out'),
    )

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    id = Column(Integer, primary_key=True)
    id_guest = Column(Integer, ForeignKey('guest.id'))
    id_room = Column(Integer, ForeignKey('room.id'))
    reserved = Column(DateTime, nullable=False, server_default=func.now())
    guests = Column(Integer, nullable=False, default=1)
    check_in = Column(Date, nullable=False, index=True)
    check_out = Column(Date, nullable=False, index=True)
    checked_in = Column(DateTime)
    checked_out = Column(DateTime)
    cancelled = Column(DateTime, default=None)
    base_price = Column(Float, nullable=False, default=0)
    taxes_percentage = Column(Float, nullable=False, default=0)
    taxes_value = Column(Float, nullable=False, default=0)
    total_price = Column(Float, nullable=False, default=0)
    locator = Column(String(50), nullable=False, index=True, unique=True)
    pin = Column(String(50), nullable=False)
    status = Column(Enum(BookingStatus), nullable=False, default='New')
    meal_plan = Column(Enum(BookingMealPlan), nullable=False,
                       default='BedAndBreakfast')
    additional_services = Column(HSTORE, default={})
    uuid = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True,
                  server_default=text('uuid_generate_v4()'),
                  default=uuid4,
                  comment='Unique code used to detect duplicates')
    deleted = Column(DateTime, default=None)

    # room = relationship("Room", backref="booking")
    # guest = relationship("Guest", backref="booking")

    def __repr__(self):
        return "<Booking(id='%s', nights='%s', guests='%s', check_in='%s', check_out='%s')>" % (
            self.id, self.nights, self.guests, self.check_in, self.check_out)

    @hybrid_property
    def nights(self):
        return (self.check_out - self.check_in).days
