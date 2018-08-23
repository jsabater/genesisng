from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Base
from schema import login
from schema import guest

engine = create_engine('postgresql://genesis@127.0.0.1/genesis', echo=True)
engine.connect()

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

l = login.Login(username='jsabater', password='password', name='Jaume',
        surname='Sabater', email='jsabater@gmail.com', is_admin=True)

session.add(l)

ll = session.query(login.Login).filter_by(email='jsabater@gmail.com').first()

print ll
