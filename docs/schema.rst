Schema package reference
========================

Model classes are contained into the `schema` package and split into modules.
They have all been defined using `SQLAlchemy's declarative model`_.

A number of PostgreSQL and SQLAlchemy features have been used, as well as some
useful Python libraries, such as:

* Enumerate types.
* UUID and JSON types.
* Date range operators.
* GIN indexes.
* Check, unique and exclude constraints.
* Hybrid properties and hybrid expressions.
* Libraries to generate random strings of variable length.

.. _SQLAlchemy's declarative model: https://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/

.. automodule:: genesisng
   :members:

.. automodule:: genesisng.schema
   :members:

.. automodule:: genesisng.schema.base
   :members:

The login module
----------------

.. automodule:: genesisng.schema.login
   :members:

The guest module
----------------

.. automodule:: genesisng.schema.guest
   :members:

The room module
---------------

.. automodule:: genesisng.schema.room
   :members:

The rate module
---------------

.. automodule:: genesisng.schema.rate
   :members:

The booking module
------------------

.. automodule:: genesisng.schema.booking
   :members:

The extras module
------------------

.. automodule:: genesisng.schema.extra
   :members:

