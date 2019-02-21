# Genesis Next-Generation

A prototype application to demonstrate the many features of Zato. Roughly based
upon the Java project [genesis](https://bitbucket.org/jsabater/genesis), it
features a back-end for a boutique hotel management system. Many of its
features are not supposed to make strict sense in the real world, but rather
show how a functionality is meant to be used or its possibilities.

## Overview

The application is prepared to be deployed as a package through
[pip](https://pypi.org/project/pip/) and contains the following modules:

* `schema`
* `services`

`schema` contains the database schema of the application. It's been tested with
PostgreSQL version 9 and 10.

`services` contains the Zato services to be hot-deployed.

## Installation

This is the software used:

* [Zato 3.0](http://zato.io/)
* [PostgreSQL 9.x and above](http://www.postgresql.org/)

These are the libraries used:

* [SQLAlchemy](http://www.sqlalchemy.org/)

### PostgreSQL configuration

As `postgres` user, edit `pg_hba.conf` and allow access to the `genesisng`
database by the `genesisng` user through IPv4 local:

```
# IPv4 local connections:
host    genesisng       genesisng       127.0.0.1/32            trust
host    all             all             127.0.0.1/32            md5
```

Reload *PostgreSQL* for the changes to take effect.

Optionally, depending on your installation, as `postgres` user, edit
`postgresql.conf` to allow connections through TCP and to log all statements
sent to the database:

```
listen_addresses = '127.0.0.1'
log_min_duration_statement = 0
```
Restart *PostgreSQL* for the changes to take effect.

As `postgres` user, add the `HSTORE`, `uuid-ossp`, `PG_TRGM`, `pgcrypto` and
[`pg_hashids`](https://github.com/iCyberon/pg_hashids) extensions to the
`template1` database, then create the `genesisng` user and database. The
`hashids` extension is only necessary if you plan on using the test data.

```
#!bash
psql --dbname=template1 --command="CREATE EXTENSION HSTORE"
psql --dbname=template1 --command="CREATE EXTENSION PG_TRGM"
psql --dbname=template1 --command='CREATE EXTENSION "uuid-ossp"'
psql --dbname=template1 --command="CREATE EXTENSION pgcrypto"
psql --dbname=template1 --command="CREATE EXTENSION pg_hashids"
createuser --no-createdb --no-createrole --no-superuser genesisng
createdb --encoding=UTF8 --owner=genesisng --template=template1 genesisng
```
As your user, create the schema:

```
cd /path/to/genesisng
python create_schema.py
```

Optionally, as your user, populate the schema with test data:

`psql --host=127.0.0.1 --username=genesisng --dbname=genesisng < path/to/genesisng/genesisng/sql/schema_data.sql`

Use this command to connect to the database from the console:

`psql --host=127.0.0.1 --username=genesisng --dbname=genesisng`

### Zato configuration

* User config
* Extra paths
* Channels
* Hot deploy services

## Current features

CRUD on login, guest, room and rate. Get all bookings from guest.
