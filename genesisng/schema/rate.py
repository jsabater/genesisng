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
    """
    Model class to represent a pricing rate in the system.

    Uses a unique constraint on the combination of the start date and the end
    date to prevent duplicated rates. It also uses a check constraint to ensure
    the start date is always before in time than the end date of the affected
    period. Finally, it uses an exclude constraint on the start date and the
    end date to prevent dates from overlapping.
    """

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

    id = Column(Integer, primary_key=True)
    """Primary key. Autoincrementing integer."""
    date_from = Column(Date, nullable=False)
    """Start date of the affected period of time."""
    date_to = Column(Date, nullable=False)
    """End date of the affected period of time."""
    base_price = Column(Float, default=0)
    """Base price for this rate to be used in calculations. Defaults to 0."""
    bed_price = Column(Float, default=0)
    """The price per bed to be added to the base price. Defaults to 0."""
    published = Column(Boolean, default=False)
    """Whether this rate is active or inactive. Defaults to False."""

    @hybrid_property
    def days(self):
        """The number of days in the date range of this rate."""
        return (self.date_to - self.date_from).days

    def __repr__(self):
        """String representation of the object."""
        return "<Rate(id='%s', date_from='%s', date_to='%s', published='%s')>" % (
            self.id, self.date_from, self.date_to, self.published)
