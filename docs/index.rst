Genesis Next-Generation's documentation
=======================================

This is the documentation of the Genesis Next-Generation project.

Genesis NG, roughly based upon the Java project `Genesis`_, is a prototype
application to demonstrate the many features of `Zato`_ and `SQLAlchemy`_. It
features a services back-end for a boutique hotel management system as a REST
API. Many of its features are not supposed to make strict sense in the real
world, but rather show how a functionality is meant to be used or its
possibilities.

.. _Genesis: https://bitbucket.org/jsabater/genesis
.. _Zato: https://zato.io/
.. _SQLAlchemy: https://www.sqlalchemy.org/

It also takes the chance to experiment with a number of ways of dealing with
classic problems or situations in similar business, such as generation of codes
or locators that are made public through emails or URLs.

Moreover, it also experiments with a number of features available in
`PostgreSQL`_, such as the `UUID`_ or `JSON`_ types, and in SQLAlchemy, such as
hybrid properties and declaration of complex schemas and indexes.

.. _PostgreSQL: https://www.postgresql.org/
.. _UUID: https://www.postgresql.org/docs/current/datatype-uuid.html
.. _JSON: https://www.postgresql.org/docs/current/datatype-json.html

The features used from those that Zato offers are:

* Import configuration through the console command ``zato enmasse``.
* Use of channels.
* Use of the pub/sub architecture.
* Use of database connections.
* Use of services.
* Use of services that invoke other services and reuse sessions.
* Use of the cache API (built-in).

Documentation of services and classes
-------------------------------------

.. toctree::
   :maxdepth: 2

   schema
   services

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
