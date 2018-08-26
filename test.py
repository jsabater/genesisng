# coding: utf8
import configparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Base
from schema import login

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')
database_uri = config['database']['URI']
echo = config['database']['echo'] == 'True'

# Connect to database
engine = create_engine(database_uri, echo=echo)
engine.connect()

Session = sessionmaker(bind=engine)
session = Session()

l = login.Login(username='jsabater', password='password', name='Jaume',
        surname='Sabater', email='jsabater@gmail.com', is_admin=True)

session.add(l)

ll = session.query(login.Login).filter_by(email='jsabater@gmail.com').first()

print ll
