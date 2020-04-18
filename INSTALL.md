# Installation of `genesisng` on Ubuntu 18.04

## Overview

The application is prepared to be deployed as a package through
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

```bash
psql --dbname=template1 --command="CREATE EXTENSION PG_TRGM"
psql --dbname=template1 --command='CREATE EXTENSION "uuid-ossp"'
psql --dbname=template1 --command="CREATE EXTENSION pgcrypto"
```

If you plan on using the provided test data to fill in the database, then you
will also need the [`pg_hashids`](https://github.com/iCyberon/pg_hashids)
extension, which must be downloaded, compiled from sources and installed
manually.

To do so, first, as your user:

```bash
cd /usr/local/src
sudo git clone https://github.com/iCyberon/pg_hashids.git
cd pg_hashids
sudo make
sudo make install
```

Then as `postgres` user:

`psql --dbname=template1 --command="CREATE EXTENSION pg_hashids"`

Also as `postgres` user, you can now create the `genesisng` user and database:

```bash
createuser --no-createdb --no-createrole --no-superuser genesisng
createdb --encoding=UTF8 --owner=genesisng --template=template1 genesisng
```

## Application

First of all, as your user, clone the repository:

```bash
cd path/to/your/projects
git clone git@github.com:jsabater/genesisng.git
cd genesisng
```

Install some Python 3 system packages:

`sudo apt install --yes python3 python3-dev python3-pip python3-venv python3-wheel`

Install the system packages required by the project:

`cat requirements.Debian | xargs sudo apt install --yes`


Configure a virtual environment for the project:

```
mkdir --parent ~/venvs/genesisng
python3 -m venv ~/venvs/genesisng
source ~/venvs/genesisng/bin/activate
```

Optionally, set something like this at the end of your `~/.bashrc` file:

```bash
VENV_HOME=$HOME/venvs
if [ -d "$HOME/path/to/genesisng" ]; then
    alias genesisng='cd ~/path/to/genesisng && source ${VENV_HOME}/genesisng/bin/activate'
fi
```

Upgrade `pip` and `wheel` (inside the virtualenv of the project):

`python3 -m pip install --upgrade pip wheel`

Install the Python packages required by the project (inside the virtualenv):

`python3 -m pip install --requirement requirements.txt`

Create the schema:

`python create_schema.py`

Optionally, populate the schema with test data:

`psql --host=localhost --username=genesisng --dbname=genesisng < path/to/genesisng/genesisng/sql/schema_data.sql`

Use this command to connect to the database from the console:

`psql --host=localhost --username=genesisng --dbname=genesisng`

## Zato configuration

The next step is to install the `genesisng`application package inside the
Docker container and let Zato have access to it.

A fresh installation can be done by using Git VCS or by copying all the
necessary files and directories. Inside the Docker container, as `root`:

apt install --yes git
cd /opt
git clone https://github.com/jsabater/genesisng

Change ownership of the repository to the `zato` user:

`chown --recursive zato.zato /opt/genesisng`

Install the package in development mode:

```
su - zato
cd /opt/genesisng
pip3 install --editable .
```

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
