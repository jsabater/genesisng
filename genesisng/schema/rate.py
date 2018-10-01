# coding: utf8
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from .base import Base
from sqlalchemy import Column, Boolean, Integer, Float, Date
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.elements import quoted_name


class Rate(Base):
    __tablename__ = 'rate'
    __rels__ = []
    __table_args__ = (
        UniqueConstraint(
            'date_from', 'date_to', name='rate_date_from_date_to'),
        CheckConstraint('date_from < date_to'),
        # Prevent dates from overlapping by using an exclusion constraint and
        # the overlap operator (&&) for the daterange type
        ExcludeConstraint((Column(
            quoted_name('daterange(date_from, date_to)', quote=False)), '&&'),
                          using='gist',
                          name='rate_date_range'),
    )

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    id = Column(Integer, primary_key=True)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    base_price = Column(Float, default=0)
    bed_price = Column(Float, default=0)
    published = Column(Boolean, default=False)

    def __repr__(self):
        return "<Rate(id='%s', date_from='%s', date_to='%s', published='%s')>" % (
            self.id, self.date_from, self.date_to, self.published)

    @hybrid_property
    def days(self):
        """Return the number of days in the date range of this rate."""
        return (self.date_to - self.date_from).days
