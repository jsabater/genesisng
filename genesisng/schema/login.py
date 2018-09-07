# coding: utf8
from genesisng.schema import Base
from sqlalchemy import Column, Boolean, Integer, String
from sqlalchemy import UniqueConstraint, Index
from sqlalchemy.dialects import postgresql

class Login(Base):
    __tablename__ = 'login'
    __rels__ = []
    __table_args__ = (
        Index('ix_trgm_login_username', 'username', postgresql_using='gin', postgresql_ops={'username': 'gin_trgm_ops'}),
        Index('ix_trgm_login_name', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('ix_trgm_login_surname', 'surname', postgresql_using='gin', postgresql_ops={'surname': 'gin_trgm_ops'}),
    )

    id = Column(Integer, primary_key=True)
    username = Column(String(20), index=True, unique=True)
    password = Column(String(255))
    name = Column(String(50))
    surname = Column(String(50))
    email = Column(String(255), index=True, unique=True)
    is_admin = Column(Boolean, default=False)

    def __repr__(self):
        return "<Login(id='%s', username='%s', name='%s', surname='%s', email='%s')>" % (
            self.id, self.username, self.name, self.surname, self.email)
