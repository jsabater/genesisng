# coding: utf8
from .base import Base
from sqlalchemy import Column, Integer, Float, String, DateTime, func
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects import postgresql
from datetime import datetime
from time import mktime
from hashids import Hashids


def generate_code(context):
    """Generates a lowercased 6-letter hashed value for the code attribute
    using the Hashids library."""

    # p = context.get_current_parameters()
    hashids = Hashids(min_length=6, salt='Evelyn Salt')
    dt = datetime.now().timetuple()
    ts = mktime(dt)
    # Python 3
    # ts = datetime.now().timestamp()
    return hashids.encode(int(ts))


class Room(Base):
    """
    Model class to represent a room in the system.

    Includes b-tree indexes to compare, sort and reduce memory consumption
    on fields `name`, `sgl_beds`, `dbl_beds`, `code` and `deleted`.

    Uses the `hashids`_ library to create a hashed value for the code attribute
    based on the id, the floor and the room numbers.

    Uses a unique constraint on the combination of the floor number and room
    number to prevent repeated rooms. It also uses a check constraint to ensure
    the accommodates attribute is a positive integer.

    Records are not deleted from the database but instead marked as deleted
    via the :attr:`~genesisng.schema.room.Room.deleted` attribute, which
    contains a timestamp of the date and time when the record was deleted.

    .. _hashids: https://pypi.org/project/hashids/
    """

    __tablename__ = 'room'
    __rels__ = []
    __table_args__ = (
        # Combination of floor number and room number must be unique.
        UniqueConstraint('floor_no', 'room_no', name='room_floor_no_room_no'),
        # The sum of beds must be a positive integer.
        CheckConstraint('sgl_beds + dbl_beds > 0'),
    )

    id = Column(Integer, primary_key=True)
    """Primary key. Autoincrementing integer."""
    floor_no = Column(Integer, nullable=False)
    """The floor number the room is located at."""
    room_no = Column(Integer, nullable=False)
    """The room number."""
    name = Column(String(100), index=True)
    """A descriptive name of the room. Mostly used on boutique and
    rural hotels."""
    sgl_beds = Column(Integer, nullable=False, index=True, default=0)
    """The amount of single beds in the room. Defaults to 0."""
    dbl_beds = Column(Integer, nullable=False, index=True, default=0)
    """The amount of double beds in the room. Defaults to 0."""
    supplement = Column(Float, nullable=False, default=0)
    """An amount to be added to the total price per day based on whatever
    random criteria the owner of the hotel wishes to use. Defaults to 0."""
    code = Column(String, nullable=False, default=generate_code,
                  unique=True, comment='Unique code used to link to images')
    """A unique code used to build the URL linking to the static content
    associated with this room. Generated through a trigger."""
    created = Column(DateTime, default=datetime.now, server_default=func.now())
    """Date and time when the room was created. Defaults to now."""
    last_updated = Column(DateTime, default=None, onupdate=datetime.now)
    """Date and time of the last update of the record. Defaults to None on
    insert, to now on update."""
    deleted = Column(DateTime, index=True, default=None)
    """Date and time of the deletion of the record. Defaults to None."""

    @hybrid_property
    def accommodates(self):
        """The amount of guests the room can accommodate. Used to calculate
        availability."""
        return self.sgl_beds + self.dbl_beds * 2

    @accommodates.expression
    def accommodates(cls):
        return (cls.sgl_beds + cls.dbl_beds * 2)

    @hybrid_property
    def number(self):
        """The room number, made of the floor number and the two digits room
        number (i.e. left-padded with a zero if needed)."""
        return '%d%02d' % (self.floor_no, self.room_no)

    @number.expression
    def number(cls):
        return (func.cast(cls.floor_no, postgresql.TEXT) +
                func.lpad(func.cast(cls.room_no, postgresql.TEXT), 2, '0'))

    def __repr__(self):
        """String representation of the object."""
        return "<Room(id='%s', name='%s', number='%s', accommodates='%s')>" % (
            self.id, self.name, self.number, self.accommodates)
