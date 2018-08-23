# coding: utf8
from schema import Base
from sqlalchemy import Column, Integer, Float, String, Date
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property

class Room(Base):
    __tablename__ = 'room'
    __rels__ = []
    __table_args__ = (
        UniqueConstraint('floor_no', 'room_no', name='room_floor_no_room_no'),
        CheckConstraint('sgl_beds + dbl_beds > 0'),
    )

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    id = Column(Integer, primary_key=True)
    floor_no = Column(Integer, nullable=False)
    room_no = Column(Integer, nullable=False)
    name = Column(String(100), index=True)
    sgl_beds = Column(Integer, default=0, index=True)
    dbl_beds = Column(Integer, default=0, index=True)
    supplement = Column(Float, nullable=False)
    code = Column(String(20), unique=True, nullable=False, comment='Unique code used to link to images')
    deleted = Column(Date, default=None)

    def __repr__(self):
        return "<Room(name='%s', floor='%s', room='%s', accommodates='%s')>" % (
            self.name, self.floor_no, self.room_no, self.accommodates)

    def __init__(self, sgl_beds, dbl_beds):
        self.sgl_beds = sgl_beds
        self.dbl_beds = dbl_beds

    @hybrid_property
    def accommodates(self):
        return self.sgl_beds + self.dbl_beds * 2

