# coding: utf8
from genesisng.schema import Base
from sqlalchemy import Column, Boolean, Integer, String
from sqlalchemy import UniqueConstraint

class Login(Base):
    __tablename__ = 'login'
    __rels__ = []
    __table_args__ = (
        UniqueConstraint('username', 'email', name='login_username_email'),
    )

    id = Column(Integer, primary_key=True)
    username = Column(String(20))
    password = Column(String(255))
    name = Column(String(50))
    surname = Column(String(50))
    email = Column(String(255))
    is_admin = Column(Boolean, default=False)

    def __repr__(self):
        return "<Login(username='%s', name='%s', surname='%s', email='%s')>" % (
            self.username, self.name, self.surname, self.email)

