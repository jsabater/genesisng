# Installation of `genesisng` on Ubuntu 18.04

## Overview

The application is prepared to be deployed as a
[wheels](https://pypi.org/project/wheel/) package through
[pip](https://pypi.org/project/pip/) and contains the following modules:

* `schema`
* `services`

`schema` contains the database schema of the application. It is designed to
work with the latest available version of PostgreSQL, although it should be
backwards compatible down to the 9.x series.

`services` contains the Zato services to be hot-deployed.

This is the software used:

* [Zato](http://zato.io/)
* [PostgreSQL](http://www.postgresql.org/)

These are the most relevant libraries used:

* [SQLAlchemy](http://www.sqlalchemy.org/) as Object-Relation Mapper (ORM)
* [Dictalchemy](https://pypi.org/project/dictalchemy/) to expand its features.
* [Hashids](http://www.hashids.org/) to create short ids from integers.
* [Nano ID](https://pypi.org/project/nanoid/) to create random short ids.
* [Sphinx](https://pypi.org/project/Sphinx/) to create the documentation.
* [Passlib](https://pypi.org/project/passlib/) to safely store passwords.

## System packages

If you don't have Git SCM, install it:

`apt install --yes git sudo`

Optionally, install a few helper applications:

`apt install --yes apt-utils ccze dialog htop mc multitail net-tools tzdata vim`

## PostgreSQL configuration

As `postgres` user, edit `pg_hba.conf` and allow access to the `genesisng`
database by the `genesisng` user through IPv4 local connections:

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

As `postgres` user, add the `HSTORE`, `uuid-ossp`, `PG_TRGM` and `pgcrypto`
extensions to the `template1` database.

```
psql --dbname=template1 --command="CREATE EXTENSION PG_TRGM"
psql --dbname=template1 --command='CREATE EXTENSION "uuid-ossp"'
psql --dbname=template1 --command="CREATE EXTENSION pgcrypto"
```

If you plan on using the provided test data to fill in the database, then you
will also need the [`pg_hashids`](https://github.com/iCyberon/pg_hashids)
extension, which must be downloaded, compiled from sources and installed
manually.

To do so, first, as your user:

```
cd /usr/local/src
sudo git clone https://github.com/iCyberon/pg_hashids.git
cd pg_hashids
sudo make
sudo make install
```

Then as `postgres` user:

`psql --dbname=template1 --command="CREATE EXTENSION pg_hashids"`

Also as `postgres` user, you can now create the `genesisng` user and database:

```
createuser --no-createdb --no-createrole --no-superuser genesisng
createdb --encoding=UTF8 --owner=genesisng --template=template1 genesisng
```

## Application repository

It is time to clone the repository and get it set up inside a virutal
environment. So, as your user, clone the repository (we'll assume we want to
keep all our projects inside `~/Projects`):

```
cd ~/Projects
git clone git@github.com:jsabater/genesisng.git
cd genesisng
```

Install some Python 3 system packages:

`sudo apt install --yes python3 python3-dev python3-pip python3-venv python3-wheel`

Install the system packages required by the project:

`cat requirements.Debian | xargs sudo apt install --yes`

Configure a virtual environment for the project (we'll assume we want to keep
them all inside `~/venvs`):

```
mkdir --parent ~/venvs/genesisng
python3 -m venv ~/venvs/genesisng
source ~/venvs/genesisng/bin/activate
```

Optionally, set something like this at the end of your `~/.bashrc` file:

```bash
if [ -d "$HOME/Projects/genesisng" ]; then
    alias genesisng='cd $HOME/Projects/genesisng && source $HOME/venvs/genesisng/bin/activate'
fi
```

Install `pep517` and upgrade `pip` and `wheel` inside the virtualenv of the
project:

`python3 -m pip install --upgrade pip wheel pep517`

Install the Python packages required by the project (inside the virtualenv):

`python3 -m pip install --requirement requirements.txt`

Optionally, create the schema:

`python create_schema.py`

Optionally, populate the schema with test data:

`psql --host=localhost --username=genesisng --dbname=genesisng < path/to/genesisng/genesisng/sql/schema_data.sql`

Use this command to connect to the database from the console:

`psql --host=localhost --username=genesisng --dbname=genesisng`

## Build and deploy the application package

The next step is to build the `genesisng` wheel package and install it inside
the Docker container and let Zato have access to it.

Build the source distribution and the binary distribution packages by using
either `setup.py`:

`python setup.py sdist bdist_wheel`

Or the `pep517` module:

`python -m pep517.build .`

In both cases you will end up with two new directories:

* `build/`: the temporary files generated by the building process.
* `dist/`: the end results.

Inside the `dist/` directory you will find two files:

```
dist
├── genesisng-0.2-py3-none-any.whl
└── genesisng-0.2.tar.gz
```

The first is the binary distribution (bdist) and the second is the source
distribution (sdist). Note that, when installing a package, `pip` installs the
source distribution by first building a wheel and then installing that, which
is the reason why we will be using the pre-built wheel when deploying the
application inside the Zato environment.

Nevertheless, whenever you want to build any of the two again, you will want a
clean build environment:

`rm --recursive --force build/ dist/`

Out last step is distributing the package by installing it. First we need to
copy it inside the Docker container:

`docker cp --archive dist/genesisng-0.2-py3-none-any.whl zato:/opt/zato/`

Inside the Docker container, as `zato` user, install the package:

`pip install genesisng-0.2-py3-none-any.whl`

This will install the package at the following location:

`/opt/zato/zato/code/lib/python3.6/site-packages/genesisng`

## Zato configuration

It is now the time to configure Zato to execute our application.

In order for the local configuration of the application to be available when
Zato executes our services, edit the configuration files of both servers
(located at `/opt/zato/env/qs-1/server1/config/repo/server.conf` and
`/opt/zato/env/qs-1/server2/config/repo/server.conf`):

```
[user_config]
# All paths are either absolute or relative to the directory server.conf is in
genesisng=/opt/zato/zato/code/lib/python3.6/site-packages/genesisng/config.ini
```

In order for Zato to know which services it has to import upon start-up, edit
the service sources files of both servers (located at
`/opt/zato/env/qs-1/server1/config/repo/service-sources.txt` and
`/opt/zato/env/qs-1/server2/config/repo/service-sources.txt`):

```
# List your service sources below, each on a separate line.
/opt/zato/zato/code/lib/python3.6/site-packages/genesisng/services
```

Restart the server for the changes to take effect. As `zato` user:

`/opt/zato/env/qs-1/zato-qs-restart.sh`

Whenever you make changes to your services and there is no need to deploy
anything else but the module containing the services, you can hot-deploy it by
copying the Python module from your development environment to the Docker
container where Zato is being executed:

```
cd ~/Projects/genesisng/src/genesisng/services
docker cp module.py zato:/opt/zato/env/qs-1/server1/pickup/incoming/services/
```

Finally, we need to use the web administration interface to configure the
following aspects:

1. An outgoing connection to the SQL database (Connections: Outgoing: SQL).
2. Cache definitions for each module (Connections: Cache: Built-in).
3. REST channels for our services (Connection: Channels: REST).

Or you can import the cluster configuration from the backup found at the
`config.yml` file. For that, first copy the file from the local repository to
the Docker container:

`docker cp --archive config.yml zato:/opt/zato/`

Then, inside the Docker container, as `zato` user, import the file:

`zato enmasse /opt/zato/env/qs-1/server1 --input /opt/zato/config.yml --import --replace-odb-objects`

If you make any changes via the web administration panel and want to export
them to keep your configuration file updated, use the following command as
`zato` user inside the Docker container:

`zato enmasse /opt/zato/env/qs-1/server1 --export-odb --dump-format yaml`

And bring it back to your local repository by using the following command:

`docker cp zato:/opt/zato/env/qs-1/config.yml ~/Projects/genesisng/`

## Execute the application

From the command line, either inside the Docker container or in your local
repository outside of the Docker container, any service can be called via
REST by using [curl](http://curl.haxx.se/):

`curl -v -g "http://localhost:11223/genesisng/guests/list"; echo ""`
