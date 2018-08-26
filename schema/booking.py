# coding: utf8
import enum
from datetime import date
from schema import Base
from sqlalchemy import Column, Integer, Float, String, Date, func
from sqlalchemy import DateTime
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

class BookingStatus(enum.Enum):
    New = 'New'
    Pending = 'Pending'
    Confirmed = 'Confirmed'
    Cancelled = 'Cancelled'
    Closed = 'Closed'

class BookingMealPlan(enum.Enum):
    RoomOnly = 'RoomOnly'
    BedAndBreakfast = 'BedAndBreakfast'
    HalfBoard = 'HalfBoard'
    FullBoard = 'FullBoard'
    AllInclusive = 'AllInclusive'
    Special = 'Special'

class Booking(Base):
    __tablename__ = 'booking'
    __rels__ = []
    __table_args__ = (
        UniqueConstraint('id_guest', 'id_room', 'check_in',
            name='booking_id_guest_id_room_check_in'),
    )

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    id = Column(Integer, primary_key=True)
    id_guest = Column(Integer, ForeignKey('guest.id'))
    id_room = Column(Integer, ForeignKey('room.id'))
    reserved = Column(DateTime, server_default=func.now())
    guests = Column(Integer)
    check_in = Column(Date, index=True)
    check_out = Column(Date, index=True)
    checked_in = Column(DateTime)
    checked_out = Column(DateTime)
    cancelled = Column(DateTime)
    base_price = Column(Float)
    taxes_percentage = Column(Float)
    taxes_value = Column(Float)
    total_price = Column(Float)
    locator = Column(String(50), index=True, unique=True)
    pin = Column(String(50))
    status = Column(Enum(BookingStatus), default='New')
    meal_plan = Column(Enum(BookingMealPlan), default='BedAndBreakfast')
    additional_services = Column(HSTORE)
    uuid = Column(String(255))
    deleted = Column(Date, default=None)

    guest = relationship('Guest')
    room = relationship('Room')

    def __repr__(self):
        return "<Booking(nights='%s', guests='%s', check_in='%s', check_out='%s')>" % (
            self.nights, self.guests, self.check_in, self.check_out)

    def __init__(self, check_in, check_out):
        self.check_in = check_in
        self.check_out = check_out

    @hybrid_property
    def nights(self):
        return (self.check_out - self.check_in).days

