# coding: utf8
import configparser
from sqlalchemy import create_engine
from genesisng.schema import *
from genesisng.schema import Base

# Load configuration
config = configparser.ConfigParser()
config.read('genesisng/config.ini')
database_uri = config['database']['URI']
echo = config['database']['echo'] == 'True'

# Connect to database
engine = create_engine(database_uri, echo=echo)
connection = engine.connect()

# Create schema
Base.metadata.create_all(engine)

# Close connection
connection.close()
