Services package reference
==========================

Services are split into modules, all contained inside the `services` package.
Each module contains a number of classes, one per service.

These services can be catalogued as tier-1 and tier-2 services, where:

* Tier-1 services are basic, CRUD-type services that work with one model class
  only in order to handle records of such entity in the database.
* Tier-2 services use tier-1 services to offer more complex functionality, such
  as the creation of a new reservation, and may pass on a session to keep all
  SQL sentences inside a single transaction.

Current tier-2 services are:

* :class:`~genesisng.services.guest.Bookings`, used to get a list of bookings
  of a guest.
* :class:`~genesisng.services.availability.Confirm`, used to create a new
  reservation and its associated guest.

Services named `List` in each module are used to get a collection of records
from the associated table and allow the following REST API-like features:

* Pagination, using a page number and a page size.
* Sorting, using a direction and a criteria.
* Filtering, which allows multiple filters and operators.
* Fields projection, which lets the developer choose which fields from the
  model class are to be returned.
* Search, which are case insensitive and take just one term.

.. automodule:: genesisng
   :members:

.. automodule:: genesisng.services
   :members:

.. _SimpleIO: https://zato.io/docs/progguide/sio.html

The login module
----------------

.. automodule:: genesisng.services.login
   :members:

The guest module
----------------

.. automodule:: genesisng.services.guest
   :members:

The room module
---------------

.. automodule:: genesisng.services.room
   :members:

The rate module
---------------

.. automodule:: genesisng.services.rate
   :members:

The booking module
------------------

.. automodule:: genesisng.services.booking
   :members:

The extra module
----------------

.. automodule:: genesisng.services.extra
   :members:

The availability module
-----------------------

.. automodule:: genesisng.services.availability
   :members:

