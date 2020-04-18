# Setting up a Zato test environment on Ubuntu 18.04

_Tested with Ubuntu 18.04 (bionic), Zato 3.1 and Python 3.6.9._

These are the necessary steps to set up a test environment for Zato running on
Python 3 inside a Docker container. PostgreSQL (for Zato’s SQL Operational
Database) and Redis (for Zato’s Key/Value Database) are kept outside of the
container for my convenience.

## Redis

Install from the distribution sources (version 4.0.9):

```sudo apt install --yes redis-server```

The default configuration binds Redis to the localhost IP address, which is
just what we need. Nonetheless, to test access to it the following command can
be issued:

```bash
$ redis-cli -h localhost -p 6379 ping
PONG
```

If in the need to reinstall Zato you will most probably have to delete all keys
from all existing databases, which can be done through the following command:

```bash
$ redis-cli -h localhost -p 6379 flushall
OK
```

## PostgreSQL

Install from the [PostgreSQL Global Development
Group](https://wiki.postgresql.org/wiki/Apt) APT repository (version 12).

Create the file `/etc/apt/sources.list.d/pgdg.list` and add the following line to it:

```deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main```

Import the repository signing key, and update the package lists:

```bash
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
```

Install PostgreSQL:

`sudo apt-get install postgresql-12 postgresql-client-12 postgresql-server-dev-12`

Edit `/etc/postgresql/12/main/pg_hba.conf` to add access rules:

```
# IPv6 local connections:
host    zato            zato            ::1/128                 trust
host    all             all             ::1/128                 md5
```

And reload the server:

```sudo service postgresql reload```

Create the user and the database. As `postgres` user:

```bash
createuser --no-createdb --no-createrole --no-superuser zato
createdb --encoding=UTF8 --owner=zato --template=template0 zato
```

In case of having to reinstall Zato it will be necessary to recreate the zato
database, which can be done through the following commands:

```
dropdb zato
createdb --encoding=UTF8 --owner=zato --template=template0 zato
```

## Docker

Install Docker, as per instructions at [Digital Ocean](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04):

```bash
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt update
sudo apt-cache policy docker-ce
sudo apt install docker-ce
sudo systemctl status docker
```

Add your username to the docker group so there’s no need to use sudo to launch
the container:

`sudo usermod -aG docker ${USER}`

Apply the changes:

`su - ${USER}`

## Ubuntu image inside Docker

Install the Ubuntu 18.04 Docker official image from its
[hub](https://hub.docker.com/_/ubuntu):

`docker pull ubuntu:18.04`

Run the container. Given that it is for for testing purposes, we can just run
the container using the network host mode instead of publishing ports:

`docker run --interactive --tty --network="host" --name zato ubuntu:18.04`

You are now `root` inside the container.

`root@myhostname:/#`

From outside of the container, use the `docker` command to find out the id and
check the name of the container:

```bash
$ docker ps --all
CONTAINER ID   IMAGE          COMMAND       CREATED              STATUS              PORTS   NAMES
886355a5e310   ubuntu:18.04   "/bin/bash"   About a minute ago   Up About a minute           zato
```

Whenever you exit the container (using the exit command), you can start it again with the following command:

`docker start --interactive zato`

And you can stop the container from outside with the following command:

`docker stop zato`

You can get a bash terminal, as `root` user, with the following command:

`docker exec --user root --interactive --tty zato bash`

## Zato inside Docker using the Ubuntu image

Update the packages list and, optionally, upgrade the installed packages:

```bash
apt update
apt upgrade --yes
```

Install a number of dependencies in the form of system packages:

`apt install --yes python3 python3-dev python3-pip git`

Optionally, install some helpers also as system packages:

`apt install --yes apt-utils ccze dialog htop mc net-tools sudo tzdata vim`

Create the `zato` user and set a password:

```bash
groupadd zato
useradd --comment "Zato Enterprise Service Bus" --home-dir /opt/zato --create-home --shell /bin/bash --gid zato zato
adduser zato sudo
passwd zato
```

Become zato and clone the repository:

```bash
su - zato
git clone https://github.com/zatosource/zato
```

Compile and install:

```bash
cd zato
./code/install.sh -p python3
```

To test that the connection from inside the container to PostgreSQL is working
fine, use the following commands:

```bash
$ sudo apt install --yes postgresql-client
$ psql --host=localhost --username=zato --dbname=zato --tuples-only --no-align --command="SELECT 1"
1
```

Please note that the previous command will install the PostgreSQL client
version 10.12, which should have no problem connecting to a more modern server.
To test that the connection from inside the container to PostgreSQL is working
fine, use the following commands:

```bash
$ sudo apt install --yes redis-tools
$ redis-cli -h localhost -p 6379 ping
PONG
```

## Zato cluster

Create a cluster using the quickstart option:

```bash
$ mkdir --parents /opt/zato/env/qs-1
$ /opt/zato/zato/code/bin/zato quickstart create --odb_host localhost --odb_port 5432 --odb_user zato --odb_db_name zato --odb_password '' --kvdb_password '' /opt/zato/env/qs-1/ postgresql localhost 6379
[1/9] Certificate authority created
[2/9] ODB schema created
[3/9] ODB initial data created
[4/9] server1 created
[5/9] server2 created
[6/9] Load-balancer created
Superuser created successfully.
[7/9] Web admin created
[8/9] Scheduler created
[9/9] Management scripts created
Quickstart cluster quickstart-726934 created
Web admin user:[admin], password:[9bR3Ith8w4LePItJ-8eulU9VgNnH4L8s]
Start the cluster by issuing the /opt/zato/env/qs-1/zato-qs-start.sh command
Visit https://zato.io/support for more information and support options
```

Edit the `zato` user’s profile file `~/.profile` to add the binaries to the
path:

```bash
# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/zato/code/bin" ] ; then
    PATH="$HOME/zato/code/bin:$PATH"
fi
```

Re-log as the `zato` user or reload the configuration:

`source ~/.profile`

Change the given password for the `admin` user, that will be required when
accessing the web administration panel, by using the following command:

```bash
$ zato update password --password <your-password> ~/env/qs-1/web-admin/ admin
Changing password for user 'admin'
OK
```

Start the cluster to test that the installation was correct:

```bash
$ /opt/zato/env/qs-1/zato-qs-start.sh
Starting Zato cluster quickstart-726934
Checking configuration
[1/8] Redis connection OK
[2/8] SQL ODB connection OK
[3/8] Checking TCP ports availability
[4/8] Load-balancer started
[5/8] server1 started
[6/8] server2 started
[7/8] Scheduler started
[8/8] Web admin started
Zato cluster quickstart-726934 started
Visit https://zato.io/support for more information and support options

$ ps --user zato x
  PID TTY      STAT   TIME COMMAND
   44 pts/0    S      0:00 -su
  131 pts/0    S      0:02 /opt/zato/zato/code/bin/python -m zato.agent.load_balancer.main /opt/zato/env/qs-1/load-balancer/config/repo fg=FalseZATO_ZATO_ZATOsync_internal=FalseZATO_ZATO_ZATOsecret_key=
  173 ?        Ss     0:00 haproxy -D -f /opt/zato/env/qs-1/load-balancer/config/repo/zato.config -p /opt/zato/env/qs-1/load-balancer/pidfile
  191 pts/0    Sl     0:02 gunicorn: master [gunicorn]
  232 pts/0    Sl     0:02 gunicorn: master [gunicorn]
  275 pts/0    Sl     0:02 /opt/zato/zato/code/bin/python -m zato.scheduler.main fg=FalseZATO_ZATO_ZATOsync_internal=FalseZATO_ZATO_ZATOsecret_key=
  307 pts/0    S      0:02 /opt/zato/zato/code/bin/python -m zato.admin.main fg=FalseZATO_ZATO_ZATOsync_internal=FalseZATO_ZATO_ZATOsecret_key=
  353 pts/0    R+     0:00 ps -u zato x
```

Connect to the admin panel at `http://localhost:8183/` and log in with the
`admin` username, then start the necessary configuration.
