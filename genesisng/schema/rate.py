# coding: utf8
from genesisng.schema import Base
from sqlalchemy import Column, Boolean, Integer, Float, Date
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from psycopg2.extras import DateRange
from sqlalchemy.sql.elements import quoted_name


class Rate(Base):
    __tablename__ = 'rate'
    __rels__ = []
    __table_args__ = (
        UniqueConstraint('date_from', 'date_to',
                         name='rate_date_from_date_to'),
        CheckConstraint('date_from < date_to'),
        # Prevent dates from overlapping by using an exclusion constraint and
        # the overlap operator (&&) for the daterange type
        ExcludeConstraint(
            (Column(quoted_name('daterange(date_from, date_to)',
                                quote=False)), '&&'),
            using='gist', name='rate_date_range'
        ),
    )

    # SQLAlchemy automatically creates the table column using the SERIAL type
    # which triggers the creation of a sequence automatically.
    id = Column(Integer, primary_key=True)
    date_from = Column(Date)
    date_to = Column(Date)
    base_price = Column(Float)
    bed_price = Column(Float)
    published = Column(Boolean, default=False)

    def __repr__(self):
        return "<Rate(id='%s', date_from='%s', date_to='%s', published='%s')>" % (
            self.id, self.date_from, self.date_to, self.published)

    def __init__(self, date_from, date_to):
        self.date_from = date_from
        self.date_to = date_to

    @hybrid_property
    def date_range(self):
        return DateRange(self.date_from, self.date_to)
