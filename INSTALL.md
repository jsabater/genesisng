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

`apt install --yes git`

Optionally, install a few helper applications:

`apt install --yes apt-utils ccze dialog htop mc multitail net-tools sudo tzdata vim`

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

**OLD VERSION - NEEDS UPDATING**

Make the package available to Zato as an extra path to the library:

`ln --symbolic /opt/genesisng /opt/zato/zato/code/zato_extra_paths/genesisng`

Edit the configuration files of both servers (located at
`/opt/zato/env/qs-1/server1/config/repo/server.conf` and
`/opt/zato/env/qs-1/server2/config/repo/server.conf`) to add the application
local configuration file:

```
[user_config]
# All paths are either absolute or relative to the directory server.conf is in
genesisng=/opt/genesisng/genesisng/config.ini
```

Restart the server for the changes to take effect. As `zato` user:

`/opt/zato/env/qs-1/zato-qs-restart.sh`

From the working copy of the repository outside of the Docker container
(`~/path/to/genesisng`), hot-deploy the services:

```
cd ~/path/to/genesisng
for f in genesisng/services/*.py; do docker cp $f zato:/opt/zato/env/qs-1/server1/pickup/incoming/services/; done
```

Load the cluster configuration from the backup found at the `config.yml` file.
This will restore the following configuration items:

* User configuration
* Extra paths
* Channels

`zato enmasse /opt/zato/env/qs-1/server1 --input /opt/genesisng/config.yml --import --replace-odb-objects`

This configuration was originally created manually through the web admin panel
and later exported into a file by executing the following command:

`zato enmasse /opt/zato/env/qs-1/server1 --export-odb --dump-format yaml`

Finally, it was copied to the repository outside of the Docker container by
using the following command:

`docker cp zato:/opt/zato/env/qs-1/config.yml ~/path/to/genesisng/`
