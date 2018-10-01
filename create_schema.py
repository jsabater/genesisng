# coding: utf8
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import configparser
from sqlalchemy import create_engine
from genesisng import schema


# Load configuration
config = configparser.ConfigParser()
config.read('genesisng/config.ini')
database_uri = config['database']['URI']
echo = config['database']['echo'] == 'True'

# Connect to database
engine = create_engine(database_uri, echo=echo)
connection = engine.connect()

# Create schema
schema.base.Base.metadata.create_all(engine)

# Close connection
connection.close()
