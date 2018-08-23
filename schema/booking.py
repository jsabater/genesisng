# coding: utf8
from schema import Base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class BookingStatus(ENUM):
    name = 'BookingStatus'
    new = 'New'
    pending = 'Pending'
    confirmed = 'Confirmed'
    cancelled = 'Cancelled'
    closed = 'Closed'

class BookingMealPlan(ENUM):
    name = 'BookingMealPlan'
    room_only = 'RoomOnly'
    bed_and_breakfast = 'BedAndBreakfast'
    half_board = 'HalfBoard'
    full_board = 'FullBoard'
    all_inclusive = 'AllInclusive'
    special = 'Special'

class Booking(Base):
    __tablename__ = 'booking'
    __rels__ = ['guest']
    __table_args__ = () 

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    id = Column(Integer, primary_key=True)
    id_guest = Column(Integer, ForeignKey('guest.id'))
    deleted = Column(Date, default=None)

    guest = relationship('Guest', backref='booking')

    def __repr__(self):
        return "<Booking(id_guest='%s', id_room='%s', nights='%s', guests='%s',
            check_in='%s', check_out='%s')>" % (self.id_guest, self.id_room,
            self.nights, self.guests, self.check_in, self.check_out)


