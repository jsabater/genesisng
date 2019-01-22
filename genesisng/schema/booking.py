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
from hashids import Hashids
import random
# from sqlalchemy.orm import relationship


class BookingStatus(str, enum.Enum):
    """
    Enumeration that uses the `enum34`_ backport library to support the
    statuses of a booking.

    Possibles values are ``New``, ``Pending``, ``Confirmed``, ``Cancelled``
    and ``Closed``.

    Additionally, it also inherits from ``str`` to make JSON serialization
    possible.

    .. _enum34: https://pypi.org/project/enum34/
    """

    New = 1
    Pending = 2
    Confirmed = 3
    Cancelled = 4
    Closed = 5


class BookingMealPlan(str, enum.Enum):
    """
    Enumeration that uses the `enum34`_ backport library to support the
    meal plans of a reservation.

    Possibles values are ``RoomOnly``, ``BedAndBreakfast``, ``HalfBoard``,
    ``FullBoard``, ``AllInclusive`` and ``Special``.

    Additionally, it also inherits from ``str`` to make JSON serialization
    possible.

    .. _enum34: https://pypi.org/project/enum34/
    """

    RoomOnly = 1
    BedAndBreakfast = 2
    HalfBoard = 3
    FullBoard = 4
    AllInclusive = 5
    Special = 6


def generate_locator(context):
    """Generates a lowercased 6-letter hashed value for the locator attribute.
    """
    p = context.current_parameters
    # hashids = Hashids(salt=p.get('nights'))
    hashids = Hashids(min_length=6, alphabet='abcdefghijklmnopqrstuvwxyz')
    return hashids.encode(p.get('id'), p.get('id_guest'), p.get('id_room'))


def generate_pin(context):
    """Generates a 4-digit Personal Identification Number (PIN) for the pin
    attribute, as a string."""
    return '%04d' % random.randint(0, 9999)


class Booking(Base):
    """
    Model class to represent a booking in the system.

    Uses a unique constraint on the combination of the check-in date, the guest
    id and the room id to prevent duplicated reservations. It also uses a check
    constraint to ensure the check-in date is always before in time than the
    check-out date.

    TODO: Add an exclude constraint on the check-in and check-out dates to
    prevent dates from overlapping.

    Includes b-tree indexes to compare, sort and reduce memory consumption
    on fields `check_in`, `check_out`, `locator`, `status`, `meal_plan` and
    `deleted`.

    Uses the `hashids`_ library to create a hashed value for the
    :attr:`~genesisng.schema.Booking.booking.locator` attribute based on the
    booking id, the guest id and the room id.

    Uses the `random`_ library to create a Personal Identification Number for
    the :attr:`~genesisng.schema.Booking.booking.pin` attribute.

    Records are not deleted from the database but instead marked as deleted
    via the :attr:`~genesisng.schema.Booking.booking.deleted` attribute, which
    contains a timestamp of the date and time when the record was deleted.

    .. _hashids: https://pypi.org/project/hashids/
    .. _random: https://docs.python.org/2/library/random.html
    """

    __tablename__ = 'booking'
    __rels__ = []
    __table_args__ = (
        # TODO: Prevent overlappings using dates as well
        UniqueConstraint('id_guest', 'id_room', 'check_in',
                         name='booking_id_guest_id_room_check_in'),
        # Never check out before checking in
        CheckConstraint('check_in < check_out'),
    )

    id = Column(Integer, primary_key=True)
    """Primary key. Autoincrementing integer."""
    id_guest = Column(Integer, ForeignKey('guest.id'))
    """Guest id. Foreign key."""
    id_room = Column(Integer, ForeignKey('room.id'))
    """Room id. Foreign key."""
    reserved = Column(DateTime, nullable=False, server_default=func.now())
    """Date and time when the reservation was placed. Defaults to now."""
    guests = Column(Integer, nullable=False, default=1)
    """The number of guests in the reservation. Defaults to 1."""
    check_in = Column(Date, nullable=False, index=True)
    """The check-in date."""
    check_out = Column(Date, nullable=False, index=True)
    """The check-out date."""
    checked_in = Column(DateTime)
    """The date and time when the guest actually checked in."""
    checked_out = Column(DateTime)
    """The date and time when the guest actually checked out."""
    cancelled = Column(DateTime, default=None)
    """The date and time when the booking was cancelled. Defaults to None."""
    base_price = Column(Float, nullable=False, default=0)
    """The base price of the booking, calculated by the availability engine and
    saved here upon creation. Defaults to 0."""
    taxes_percentage = Column(Float, nullable=False, default=0)
    """The percentage to be applied as taxes upon the base price, calculated by
    the availability engine and saved here upon creation. Defaults to 0."""
    taxes_value = Column(Float, nullable=False, default=0)
    """The value of the taxes to be added to the base price, calculated by the
    availability engine and saved here upon creation. Defaults to 0."""
    total_price = Column(Float, nullable=False, default=0)
    """The total price of the booking, calculated by the availability engine
    and saved here upon creation. Defaults to 0."""
    locator = Column(String(6), nullable=False, default=generate_locator,
                     index=True, unique=True)
    """Unique locator of the reservation."""
    pin = Column(String(4), nullable=False, default=generate_pin)
    """Personal Identification Number (PIN) for the reservation, used to
    access the client area."""
    status = Column(Enum(BookingStatus), nullable=False, index=True,
                    default='New')
    """Status of the reservation. Defaults to New."""
    meal_plan = Column(Enum(BookingMealPlan), nullable=False, index=True,
                       default='BedAndBreakfast')
    """Meal plan included in the reservation. Defaults to BedAndBreakfast."""
    additional_services = Column(HSTORE, default={})
    """Additional services included in the reservation, stored as a key/pair
    JSON document."""
    uuid = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True,
                  server_default=text('uuid_generate_v4()'),
                  default=uuid4,
                  comment='Unique code used to detect duplicates')
    """Universally Unique IDentifier of the reservation. Used to back up the
    primary key."""
    deleted = Column(DateTime, index=True, default=None)
    """Timestamp of the deletion of the record. Defaults to None."""

    @hybrid_property
    def nights(self):
        """The amount of nights the guests are staying for this booking."""
        return (self.check_out - self.check_in).days

    # room = relationship("Room", backref="booking")
    # guest = relationship("Guest", backref="booking")

    def __repr__(self):
        """String representation of the object."""
        return "<Booking(id='%s', nights='%s', guests='%s', check_in='%s', check_out='%s')>" % (
            self.id, self.nights, self.guests, self.check_in, self.check_out)
