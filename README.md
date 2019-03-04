# Genesis Next-Generation

A prototype application to demonstrate the many features of Zato. Roughly based
upon the Java project [genesis](https://bitbucket.org/jsabater/genesis), it
features a services back-end for a boutique hotel management system. Many of
its features are not supposed to make strict sense in the real world, but
rather show how a functionality is meant to be used or its possibilities.

## Overview

The application is prepared to be deployed as a package through
[pip](https://pypi.org/project/pip/) and contains the following modules:

* `schema`
* `services`

`schema` contains the database schema of the application. It's been tested with
PostgreSQL version 9.x, 10 and 11.

`services` contains the Zato services to be hot-deployed.

## Installation

This is the software used:

* [Zato 3.0](http://zato.io/)
* [PostgreSQL 9.x and above](http://www.postgresql.org/)

These are the most relevant libraries used:

* [SQLAlchemy](http://www.sqlalchemy.org/) as Object-Relation Mapper (ORM) and
    [Dictalchemy](https://pypi.org/project/dictalchemy/) to expand its features.
* [Hashids](http://www.hashids.org/) to create short ids from integers.
* [Nano ID](https://pypi.org/project/nanoid/) to create random short ids.
* [Sphinx](https://pypi.org/project/Sphinx/) to create the documentation.
* [Passlib](https://pypi.org/project/passlib/) to safely store passwords.

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
`hashids` extension is only necessary if you plan on using the test data and must be downloaded, compiled from sources and installed manually.

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

The following schema classes have been defined using SQLAlchemy's declarative
model:

* **login:** represents a user that can log into the system.
* guest: represents a guest that makes a reservation and fatures an enumerate
    type `Gender`, a hybrid property and a number of GIN indexes.
* **room:** represents a room in the system and features the use of the `Hashids`
    library to generate a unique, public code for each room, two hybrid
    properties and a check constraint.
* **rate:** represents a pricing rate in the system and features an hybrid property
    and an exclude constraint using date ranges.
* **booking:** represents a booking in the system and features two enumerate types,
    the use of the Nano ID library to generate a random, short, public locator,
    the use of the random library to create a Personal Identification Number
    (PIN), a check constraint, a hybrid property and the use of the UUID and
    JSON types.
* **extra:** represents an additional service of a booking in the system, which are
    retrieved from this table but then stored as a JSON document inside the
    `extras` column of the `booking` model class.

The application also has a number of services, spread among the following
modules. The following list summarizes the services in each module:

* **login:** `get`, `validate`, `create`, `delete`, `update` and `list`.
* **guest:** `get`, `create`, `delete`, `update` , `upsert`, `list`, `booking`
    and `restore`.
* **room:** `get`, `create`, `delete`, `restore`, `update` and `list`.
* **rate:** `get`, `create`, `delete`, `update` and `list`.
* **booking:** `get`, `locate`, `create`, `cancel`, `delete`, `update`,
    `changepin`, `validate`, `list` and `restore`.
* **availability:** `search`, `extras` and `confirm`.

Logins and rates records are deleted. The rest are marked as deleted by setting
the timestamp of deletion on the `deleted` column.

There are two types of services:

* Tier-1. Services that work with one model class only in order to create,
    delete, update, get or list records of such entity in the database.
* Tier-2. Services that use tier-1 services to offer more complex
    functionality and may pass on a session parameter to keep all SQL sentences
    inside a single transaction.

All services make use of the Cache API, using hand-crafted cache keys. Handling
of cache entries in cache collections is done in every service following the
business logic required by the application.

Some listings include a number of common features in REST API, such as:

* Pagination, using a page number and a page size.
* Sorting, using a direction and a criteria.
* Filtering, which allows multiple filters and operators.
* Fields projection, which lets the developer choose which fields from the
    model class are to be returned.
* Search, which are case insensitive and take just one term.

## Documentation

Project documentation, extracted from the code, can be generated by running
`make html` inside the `docs` subdirectory. It has been created using Sphinx,
which has been set as a project requirement.

Part of the information provided on this file is also available there.
