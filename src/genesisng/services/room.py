# -*- coding: utf-8 -*-
from contextlib import closing
from http.client import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from datetime import datetime
from bunch import Bunch
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from zato.server.service import Service, Integer, Float, List
from genesisng.schema.room import Room
from genesisng.util.config import parse_args
from genesisng.util.filters import parse_filters


class Get(Service):
    """
    Service class to get a room by id.

    Channel ``/genesisng/rooms/{id}/get``.

    Uses `SimpleIO`_.

    Stores the record in the ``rooms`` cache. Returns ``Cache-Control``,
    ``Last-Modified`` and ``ETag`` headers. Returns a ``Content-Language``
    header.

    Returns ``OK`` upon successful retrieval, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        output_optional = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code', 'name', 'accommodates',
                           'number')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the room.
        :type id: int
        :param session: A live session (transaction) to be reused.
        :type session: :class:`~sqlalchemy.orm.session.Session`

        :returns: All attributes of a :class:`~genesisng.schema.room.Room`
            model class, including the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        id_ = self.request.input.id

        # Check whether a copy exists in the cache
        cache_key = 'id:%s' % id_
        cache = self.cache.get_cache('builtin', 'rooms')
        cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.response.status_code = OK
            self.environ.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.headers['Content-Language'] = 'en'
            self.response.payload = cache_data.value
            return

        # Reuse the session if any has been provided
        if self.environ.session:
            session = self.environ.session
        else:

            session = self.outgoing.sql.get(conn).session()

        # Otherwise, retrieve the data
        result = session.query(Room).\
            filter(and_(Room.id == id_, Room.deleted.is_(None))).\
            one_or_none()

        if result:

            # Save the record in the cache
            cache_data = cache.set(
                cache_key, result.asdict(), details=True)

            # Set cache headers in response
            if cache_data:
                self.response.headers['Cache-Control'] = cache_control
                self.response.headers['Last-Modified'] = cache_data.\
                    last_write_http
                self.response.headers['ETag'] = cache_data.hash
            else:
                self.response.headers['Cache-Control'] = 'no-cache'

            # Return the result
            self.response.status_code = OK
            self.environ.status_code = OK
            self.response.headers['Content-Language'] = 'en'
            self.response.payload = cache_data.value
        else:
            self.response.status_code = NOT_FOUND
            self.environ.status_code = NOT_FOUND
            self.response.headers['Cache-Control'] = 'no-cache'
            self.response.headers['Content-Language'] = 'en'

        # Close the session only if we created a new one
        if not self.environ.session:
            session.close()


class Create(Service):
    """
    Service class to create a new room.

    Channel ``/genesisng/rooms/create``.

    Uses `SimpleIO`_.

    Stores the record in the ``rooms`` cache. Returns a ``Cache-Control``
    header.

    Returns ``CREATED`` upon successful creation, or ``CONFLICT`` otherwise.
    """

    class SimpleIO:
        input_required = (Integer('floor_no'), Integer('room_no'),
                          Integer('sgl_beds'), Integer('dbl_beds'),
                          Float('supplement'))
        input_optional = ('name')
        output_optional = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code', 'name', 'accommodates',
                           'number')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param floor_no: The floor number where the room is located.
        :type floor_no: int
        :param room_no: The room number.
        :type room_no: int
        :param sgl_beds: The number of single beds in the room.
        :type sgl_beds: int
        :param dbl_beds: The number of double beds in the room.
        :type dbl_beds: int
        :param supplement: An amount to be added to the price per day for this
            room.
        :type supplement: float
        :param name: A descriptive name for the room. Optional.
        :type name: str

        :returns: All attributes of a :class:`~genesisng.schema.room.Room`
            model class, including the hybrid properties.
        :rtype: dict
        """

        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        result = Room(
            floor_no=p.floor_no,
            room_no=p.room_no,
            sgl_beds=p.sgl_beds,
            dbl_beds=p.dbl_beds,
            supplement=p.supplement,
            name=p.get('name', None))

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(result)
                session.commit()

                # Save the record in the cache
                cache_key = 'id:%s' % result.id
                cache = self.cache.get_cache('builtin', 'rooms')
                result = result.asdict()
                cache.set(cache_key, result)

                # Return the result
                self.response.status_code = CREATED
                self.response.payload = result
                url = self.user_config.genesisng.location.rooms
                self.response.headers['Location'] = url.format(id=result['id'])
                self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraint prevents duplication of codes or room numbers.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'
                # TODO: Return well-formed error response?
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948
                # TODO: Handle duplicated codes (retry with another code).


class Delete(Service):
    """
    Service class to delete an existing room.

    Channel ``/genesisng/rooms/{id}/delete``.

    Uses `SimpleIO`_.

    Removes the record from the ``rooms`` cache, if found. Returns a
    ``Cache-Control`` header.

    Returns ``NO_CONTENT`` upon successful deletion, or ``NOT_FOUND``
    therwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        """
        Service handler.

        :param id: The id of the room.
        :type id: int

        :returns: Nothing.
        """
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Room).\
                filter(and_(Room.id == id_, Room.deleted.is_(None))).\
                one_or_none()
            if result:
                # Set deleted field
                result.deleted = datetime.utcnow()
                session.commit()
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'

                # Invalidate the cache
                cache_key = 'id:%s' % id_
                cache = self.cache.get_cache('builtin', 'rooms')
                cache.delete(cache_key)

            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Restore(Service):
    """
    Service class to restore a deleted room.

    Channel ``/genesisng/rooms/{id}/restore``.

    Uses `SimpleIO`_.

    Sets the ``deleted`` field to None if, and only if, the room exists and it
    had been previously marked as deleted.

    Stores the record in the ``rooms`` cache. Returns a ``Cache-Control``
    header.

    Returns ``OK`` upon successful restoration, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        output_optional = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code', 'name', 'accommodates',
                           'number')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the room.
        :type id: int

        :returns: All attributes of a :class:`~genesisng.schema.room.Room`
            model class.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Room).\
                filter(and_(Room.id == id_, Room.deleted.isnot(None))).\
                one_or_none()

            if result:
                # Update dictionary key
                result.deleted = None
                session.commit()

                # Save the result in the cache, as dict
                cache_key = 'id:%s' % id_
                cache = self.cache.get_cache('builtin', 'rooms')
                result = result.asdict()
                cache.set(cache_key, result)

                self.response.status_code = OK
                self.response.payload = result
                self.response.headers['Cache-Control'] = 'no-cache'
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Update(Service):
    """
    Service class to update an existing room.

    Channel ``/genesisng/rooms/{id}/update``.

    Uses `SimpleIO`_.

    Stores the updated record in the ``rooms`` cache. Returns a
    ``Cache-Control`` header. Only non-empty keys will be updated.

    Returns ``OK`` upon successful modification, ``NOT_FOUND`` if the record
    cannot be found, or ``CONFLICT`` in case of a constraint error.

    Attributes not sent through the request are not updated. Attribute ``code``
    cannot be updated, as it is generated upon, and only upon, creation.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = (Integer('floor_no'), Integer('room_no'), 'name',
                          Integer('sgl_beds'), Integer('dbl_beds'),
                          Float('supplement'))
        output_optional = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code', 'name', 'accommodates',
                           'number')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the room. Mandatory.
        :type id: int
        :param floor_no: The floor number where the room is located.
        :type floor_no: int
        :param room_no: The room number.
        :type room_no: int
        :param sgl_beds: The number of single beds in the room.
        :type sgl_beds: int
        :param dbl_beds: The number of double beds in the room.
        :type dbl_beds: int
        :param supplement: An amount to be added to the price per day for this
            room.
        :type supplement: float
        :param name: A descriptive name for the room.
        :type name: str

        :returns: All attributes of a :class:`~genesisng.schema.room.Room`
            model class, including the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                result = session.query(Room).\
                    filter(and_(Room.id == id_, Room.deleted.is_(None))).\
                    one_or_none()

                if result:
                    # TODO: Implement a wrapper to remove empty request keys,
                    # or add request params to skip_empty_keys as per
                    # https://forum.zato.io/t/leave-the-simpleio-input-optional-out-of-the-input/593/22
                    # then use dictalchemy's .fromdict() to reduce code.
                    # result.fromdict(self.request.input, allow_pk=True)

                    # Update dictionary keys
                    if p.floor_no:
                        result.floor_no = p.floor_no
                    if p.room_no:
                        result.room_no = p.room_no
                    if p.name:
                        result.name = p.name
                    if p.sgl_beds:
                        result.sgl_beds = p.sgl_beds
                    if p.dbl_beds:
                        result.dbl_beds = p.dbl_beds
                    if p.supplement:
                        result.supplement = p.supplement
                    session.commit()

                    # Save the record in the cache
                    cache_key = 'id:%s' % result.id
                    cache = self.cache.get_cache('builtin', 'rooms')
                    cache_data = cache.set(
                        cache_key, result.asdict(), details=True)

                    self.response.status_code = OK
                    self.response.payload = cache_data.value
                    self.response.headers['Cache-Control'] = 'no-cache'
                else:
                    self.response.status_code = NOT_FOUND
                    self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraint prevents duplication of room numbers and rooms
                # without accommodation.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class List(Service):
    """
    Service class to get a list of rooms in the system.

    Channel ``/genesisng/rooms/list``.

    Uses `SimpleIO`_.

    Stores the returned record set and each of the records individually in the
    ``rooms`` cache. Since the list of rooms is short, this is used every time
    the list of rooms is listed on the website or the back-office. Individual
    records are used by the ``Get`` service when viewing the details of a room.
    Returns a ``Cache-Control`` header.

    Returns ``NO_CONTENT`` if the returned list is empty, or ``OK`` otherwise.

    Sorting is always enforced. Filtering, fields projection, search and
    pagination are not allowed. Given that the result set will always be small,
    filtering is expected to be done in the controller class or in the client.

    In case of error, it does not return ``BAD_REQUEST`` but, instead, it
    assumes the default parameter values and carries on.
    """

    allowed = Bunch({
        'criteria': (),
        'filters': (),
        'fields': (),
        'search': ()
    })

    class SimpleIO:
        output_optional = ('id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                           'supplement', 'code', 'name', 'accommodates',
                           'number')
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        """
        Service handler.

        Query string parameters:

        :returns: A list of dicts with all attributes of a
            :class:`~genesisng.schema.room.Room` model class, including the
            hybrid attributes.
        :rtype: list
        """

        # Database connection
        conn = self.user_config.genesisng.database.connection

        # Cache control default value
        cache_control = self.user_config.genesisng.cache.default_cache_control

        # Check whether a copy exists in the cache
        cache_key = 'all'
        try:
            cache = self.cache.get_cache('builtin', 'rooms')
        except Exception:
            self.logger.error("Could not get the 'rooms' cache collection.")
        if cache is not None:
            cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.logger.info("Returning list of rooms from the cache.")

            self.response.status_code = OK
            self.response.payload[:] = cache_data.value
            self.response.headers['Content-Language'] = 'en'
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = str(
                cache_data.last_write_http)
            self.response.headers['ETag'] = str(cache_data.hash)
            return

        # Compose and execute query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(Room)
            query = query.order_by(Room.id.asc())
            result = query.all()

            # Return now if no rows were returned
            if not result:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'
                return

            # Empty list of dicts to be saved in the cache
            payload = []

            # Loop the result set
            for r in result:
                # Convert each WritableKeyedTuple to a dict so that we store
                # a list of dicts in the cache
                d = r._asdict()
                payload.append(d)

                # Store each full row (as a dict) in the cache.
                if cache is not None:
                    cache.set('id:%s' % r.id, d)

            # Store the processed result set in the cache
            if cache is not None:
                self.logger.info("Storing list of rooms in the cache.")
                cache_data = cache.set(cache_key, payload, details=True)

            self.response.status_code = OK
            self.response.payload[:] = payload
            self.response.headers['Content-Language'] = 'en'

            if cache_data:
                self.response.headers['Cache-Control'] = cache_control
                self.response.headers['Last-Modified'] = str(
                    cache_data.last_write_http)
                self.response.headers['ETag'] = str(cache_data.hash)
            else:
                self.response.headers['Cache-Control'] = 'no-cache'
