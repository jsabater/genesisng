# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT, FORBIDDEN
from httplib import BAD_REQUEST
from zato.server.service import Service
from zato.server.service import Integer, Float, Date, DateTime
from zato.server.service import Dict, List, AsIs
from genesisng.schema.booking import Booking, generate_pin
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime


class Get(Service):
    """
    Service class to get a booking by id.

    Channel ``/genesisng/bookings/{id}/get``.

    Uses `SimpleIO`_.

    Stores the record in the ``bookings`` cache. Returns ``Cache-Control``,
    ``Last-Modified`` and ``ETag`` headers. Returns a ``Content-Language``
    header.

    Returns ``OK`` upon successful retrieval, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO(object):
        input_required = (Integer('id'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'), 'base_price',
                           'taxes_percentage', 'taxes_value', 'total_price',
                           'locator', 'pin', 'status', 'meal_plan',
                           Dict('extras'),
                           # 'uuid' # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights'
                           )
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the booking.
        :type id: int

        :returns: All attributes of a
            :class:`~genesisng.schema.booking.Booking` model class, including
            the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        id_ = self.request.input.id

        # Check whether a copy exists in the cache
        cache_key = 'id:%s' % id_
        cache = self.cache.get_cache('builtin', 'bookings')
        cache_data = cache.get_by_prefix(cache_key, details=True, limit=1)
        if cache_data:
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.headers['Content-Language'] = 'en'
            self.response.payload = cache_data.value
            return

        # Otherwise, retrieve the data
        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_, Booking.deleted.is_(None))).\
                one_or_none()

            if result:
                # Save the record in the cache
                cache_key = 'id:%s|locator:%s' % (result.id, result.locator)
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
                self.response.payload = result
                self.response.headers['Content-Language'] = 'en'
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'


class Locate(Service):
    """
    Service class to get a booking by locator.

    Channel ``/genesisng/bookings/{locator}/locate``.

    Uses `SimpleIO`_.

    Stores the record in the ``bookings`` cache. Returns ``Cache-Control``,
    ``Last-Modified`` and ``ETag`` headers. Returns a ``Content-Language``
    header.

    Returns ``OK`` upon successful retrieval, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO(object):
        input_required = ('locator')
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'), 'base_price',
                           'taxes_percentage', 'taxes_value', 'total_price',
                           'locator', 'pin', 'status', 'meal_plan',
                           Dict('extras'),
                           # 'uuid' # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights'
                           )
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param locator: The locator of the booking.
        :type locator: str

        :returns: All attributes of a
            :class:`~genesisng.schema.booking.Booking` model class, including
            the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        locator = self.request.input.locator.lower()

        # Check whether a copy exists in the cache
        cache_key = 'locator:%s' % locator
        cache = self.cache.get_cache('builtin', 'bookings')
        cache_data = cache.get_by_suffix(cache_key, details=True, limit=1)
        if cache_data:
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.headers['Content-Language'] = 'en'
            self.response.payload = cache_data.value
            return

        # Otherwise, retrieve the data
        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.locator == locator,
                            Booking.deleted.is_(None))).\
                one_or_none()

            if result:
                # Save the record in the cache
                cache_key = 'id:%s|locator:%s' % (result.id, result.locator)
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
                self.response.payload = result
                self.response.headers['Content-Language'] = 'en'
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'


class Create(Service):
    """
    Service class to create a new booking.

    Channel ``/genesisng/bookings/create``.

    Uses `SimpleIO`_.

    Stores the record in the ``bookings`` cache. Returns a ``Cache-Control``
    header.

    Returns ``CREATED`` upon successful creation, or ``CONFLICT`` otherwise.
    """

    class SimpleIO:
        input_required = (Integer('id_guest'), Integer('id_room'),
                          Integer('guests'), Date('check_in'),
                          Date('check_out'), Float('base_price'),
                          Float('taxes_percentage'), Float('taxes_value'),
                          Float('total_price'))
        input_optional = (DateTime('checked_in'), DateTime('checked_out'),
                          DateTime('cancelled'), 'status', 'meal_plan',
                          Dict('extras'), 'uuid', AsIs('session'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           'base_price', 'taxes_percentage', 'taxes_value',
                           'total_price', 'locator', 'pin', 'status',
                           'meal_plan', Dict('extras'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'),
                           # 'uuid', # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights'
                           )
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id_guest: The id of the guest the booking belongs to.
        :type id_guest: int
        :param id_room: The id of the room the booking is associated to.
        :type id_room: int
        :param guests: The number of guests in the room. Default is 1.
        :type guests: int
        :param check_in: The date the guests of the booking will be arriving.
        :type check_in: date
        :param check_out: The date the guests of the booking will be leaving.
        :type check_out: date
        :param base_price: The base price of the booking, calculated by the
            availability engine. Default is 0.
        :type base_price: float
        :param taxes_percentage: The percentage to be applied as taxes upon the
            base price, calculated by the availability engine.
        :type taxes_percentage: float
        :param taxes_value: The amount to be added to the base price as taxes,
            calculated by the availability engine.
        :type taxes_value: float
        :param total_price: The total price of the booking, calculated by the
            availability engine.
        :type total_price: str
        :param checked_in: The date and time when the guests actually checked
            in. Optional. Default is None.
        :type checked_in: datetime
        :param checked_out: The date and time when the guests actually checked
            out. Optional. Default is None.
        :type checked_in: datetime
        :param cancelled: The date and time when the booking was cancelled.
            Optional. Default is None.
        :type cancelled: datetime
        :param status: The status of the reservation. One of the values of the
            enumerate :class:`~genesisng.schema.booking.BoookingStatus`.
            Optional. Default is ``New``.
        :type status: enum
        :param meal_plan: The meal plan for this reservation. One of the values
            of the enumerate
            :class:`~genesisng.schema.booking.BookingMealPlan`. Optional.
            Default is ``BedAndBreakfast``.
        :type meal_plan: enum
        :param extras: A dictionary with the additional services the guest has
            hired for this reservation. It will have just one key, named
            'list', with a list of dicts as value. Each dict in the list will
            have the following attributes: code, name, description and price.
            Optional. Default is {}.
        :type extras: dict

        :returns: All attributes of a
            :class:`~genesisng.schema.booking.Booking` model class.
        :rtype: dict
        """

        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection
        p = self.request.input

        try:
            datetime.strptime(p.check_in, '%Y-%m-%d').date()
            datetime.strptime(p.check_out, '%Y-%m-%d').date()
        except ValueError:
            self.response.status_code = BAD_REQUEST
            self.environ.status_code = BAD_REQUEST
            msg = 'Wrong check-in or check-out date format'
            self.environ.error_msg = msg
            self.response.payload = {'error': {'message': msg}}
            return

        # Check UUID string and convert it into an actual UUID
        # UUID is optional. If not passed, one will be created.
        if p.uuid:
            try:
                uuid = UUID(p.uuid, version=4)
            except ValueError:
                self.response.status_code = BAD_REQUEST
                self.environ.status_code = BAD_REQUEST
                msg = 'Wrong UUID format'
                self.environ.error_msg = msg
                self.response.payload = {'error': {'message': msg}}
                return
        else:
            uuid = None

        # Check the extras parameter has the correct format, i.e. a dictionary
        # with a 'list' key whose value is a list of dictionaries, each with
        # the keys 'code', 'name', 'description' and 'price'.
        if p.extras:
            try:
                for e in p.extras['list']:
                    if not {'code', 'name', 'description', 'price'} <= set(e):
                        raise
            except Exception:
                self.response.status_code = BAD_REQUEST
                self.environ.status_code = BAD_REQUEST
                msg = 'Wrong format in extras'
                self.environ.error_msg = msg
                self.response.payload = {'error': {'message': msg}}
                return

        params = {
            'id_guest': p.id_guest,
            'id_room': p.id_room,
            'guests': p.guests,
            'check_in': p.check_in,
            'check_out': p.check_out,
            'base_price': p.base_price,
            'taxes_percentage': p.taxes_percentage,
            'taxes_value': p.taxes_value,
            'total_price': p.total_price,
            'checked_in': p.checked_in,
            'checked_out': p.checked_out,
            'cancelled': p.cancelled,
            'status': p.status,
            'meal_plan': p.meal_plan,
            'extras': p.extras,
            'uuid': uuid
        }

        # Remove empty strings from params
        for k in params.keys():
            if params[k] == '':
                del(params[k])

        result = Booking().fromdict(params)

        # Reuse the session if any has been provided
        if self.request.input.session:
            session = self.request.input.session
        else:
            session = self.outgoing.sql.get(conn).session()

        try:
            session.add(result)

            # Flush if we are reusing the session, otherwise commit
            if self.environ.session:
                session.flush()
            else:
                session.commit()

            # Save the record in the cache
            cache_key = 'id:%s|locator:%s' % (result.id, result.locator)
            cache = self.cache.get_cache('builtin', 'bookings')
            result = result.asdict()
            cache.set(cache_key, result)

            self.response.status_code = CREATED
            self.environ.status_code = CREATED
            self.response.payload = result
            url = self.user_config.genesisng.location.bookings
            self.response.headers['Location'] = url.format(id=result['id'])
            self.response.headers['Cache-Control'] = 'no-cache'

        except IntegrityError:
            # Constraints prevent duplication of bookings via id_guest,
            # id_room and check_in attributes. Also checks that the
            # check-in date is before the check-out date.
            session.rollback()
            self.response.status_code = CONFLICT
            self.environ.status_code = CONFLICT
            self.response.headers['Cache-Control'] = 'no-cache'
            # TODO: Return well-formed error response
            # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948

        # Close the session only if we created a new one
        if not self.environ.session:
            session.close()


class Cancel(Service):
    """
    Service class to cancel an existing booking.

    Channel ``/genesisng/bookings/{id}/cancel``.

    Uses `SimpleIO`_.

    Stores the record in the ``bookings`` cache, if found. Returns a
    ``Cache-Control`` header.  Returns a ``Content-Language`` header.

    Returns ``OK`` upon successful cancellation, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'), 'base_price',
                           'taxes_percentage', 'taxes_value', 'total_price',
                           'locator', 'pin', 'status', 'meal_plan',
                           Dict('extras'),
                           # 'uuid' # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights'
                           )

    def handle(self):
        """
        Service handler.

        :param id: The id of the booking.
        :type id: int

        :returns: All attributes of a
            :class:`~genesisng.schema.booking.Booking` model class, including
            the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_,
                            Booking.deleted.is_(None),
                            Booking.cancelled.is_(None))).\
                one_or_none()

            if result:
                # Set cancelled field
                result.cancelled = datetime.utcnow()
                session.commit()

                # Save the record in the cache
                cache_key = 'id:%s|locator:%s' % (result.id, result.locator)
                cache = self.cache.get_cache('builtin', 'bookings')
                cache.set(cache_key, result.asdict())

                # Return the result
                self.response.status_code = OK
                self.response.payload = result
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'


class Delete(Service):
    """
    Service class to delete an existing booking.

    Channel ``/genesisng/bookings/{id}/delete``.

    Uses `SimpleIO`_.

    Removes the record from the ``bookings`` cache, if found. Returns a
    ``Cache-Control`` header.

    Returns ``NO_CONTENT`` upon successful deletion, or ``NOT_FOUND``
    therwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        """
        Service handler.

        :param id: The id of the booking.
        :type id: int

        :returns: Nothing.
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_, Booking.deleted.is_(None))).\
                one_or_none()

            if result:
                # Set deleted field
                result.deleted = datetime.utcnow()
                session.commit()
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'

                # Invalidate the cache
                cache_key = 'id:%s|locator:%s' % (result.id, result.locator)
                cache = self.cache.get_cache('builtin', 'bookings')
                cache.delete(cache_key)
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Update(Service):
    """
    Service class to update an existing booking.

    Channel ``/genesisng/bookings/{id}/update``.

    Uses `SimpleIO`_.

    Stores the updated record in the ``bookings`` cache. Returns a
    ``Cache-Control`` header. Only non-empty keys will be updated.

    Returns ``OK`` upon successful modification, ``NOT_FOUND`` if the record
    cannot be found, or ``CONFLICT`` in case of a constraint error.

    Attributes not sent through the request are not updated.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = (Integer('id_guest'), Integer('id_room'),
                          Integer('guests'), Date('check_in'),
                          Date('check_out'), DateTime('checked_in'),
                          DateTime('checked_out'), DateTime('cancelled'),
                          Float('base_price'), Float('taxes_percentage'),
                          Float('taxes_value'), Float('total_price'), 'status',
                          'meal_plan', Dict('extras'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'), 'base_price',
                           'taxes_percentage', 'taxes_value', 'total_price',
                           'locator', 'pin', 'status', 'meal_plan',
                           Dict('extras'),
                           # 'uuid' # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights'
                           )
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the booking. Mandatory.
        :type id: int
        :param id_guest: The id of the guest the booking belongs to.
        :type id_guest: int
        :param id_room: The id of the room the booking is associated to.
        :type id_room: int
        :param guests: The number of guests in the room. Default is 1.
        :type guests: int
        :param check_in: The date the guests of the booking will be arriving.
        :type check_in: date
        :param check_out: The date the guests of the booking will be leaving.
        :type check_out: date
        :param base_price: The base price of the booking, calculated by the
            availability engine..
        :type base_price: float
        :param taxes_percentage: The percentage to be applied as taxes upon the
            base price, calculated by the availability engine.
        :type taxes_percentage: float
        :param taxes_value: The amount to be added to the base price as taxes,
            calculated by the availability engine.
        :type taxes_value: float
        :param total_price: The total price of the booking, calculated by the
            availability engine.
        :type total_price: str
        :param checked_in: The date and time when the guests actually checked
            in.
        :type checked_in: datetime
        :param checked_out: The date and time when the guests actually checked
            out.
        :type checked_in: datetime
        :param cancelled: The date and time when the booking was cancelled.
        :type cancelled: datetime
        :param status: The status of the reservation. One of the values of the
            enumerate :class:`~genesisng.schema.booking.BoookingStatus`.
        :type status: enum
        :param meal_plan: The meal plan for this reservation. One of the values
            of the enumerate
            :class:`~genesisng.schema.booking.BookingMealPlan`.
        :type meal_plan: enum
        :param extras: A dictionary with the additional services
            the guest has hired for this reservation. Optional.
        :type extras: dict

        :returns: All attributes of a
            :class:`~genesisng.schema.booking.Booking` model class.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                result = session.query(Booking).\
                    filter(Booking.id == id_).one_or_none()

                if result:
                    # TODO: Implement a wrapper to remove empty request keys,
                    # or add request params to skip_empty_keys as per
                    # https://forum.zato.io/t/leave-the-simpleio-input-optional-out-of-the-input/593/22
                    # then use dictalchemy's .fromdict() to reduce code.
                    # result.fromdict(self.request.input, allow_pk=True)

                    # Update dictionary keys
                    if p.id_guest:
                        result.id_guest = p.id_guest
                    if p.id_room:
                        result.id_room = p.id_room
                    if p.guests:
                        result.guests = p.guests
                    if p.check_in:
                        result.check_in = p.check_in
                    if p.check_out:
                        result.check_out = p.check_out
                    if p.checked_in:
                        result.checked_in = p.checked_in
                    if p.checked_out:
                        result.checked_out = p.checked_out
                    if p.base_price:
                        result.base_price = p.base_price
                    if p.taxes_percentage:
                        result.taxes_percentage = p.taxes_percentage
                    if p.taxes_value:
                        result.taxes_value = p.taxes_value
                    if p.total_price:
                        result.total_price = p.total_price
                    if p.status:
                        result.status = p.status
                    if p.meal_plan:
                        result.meal_plan = p.meal_plan
                    if p.extras:
                        result.extras = p.extras
                    session.commit()

                    # Save the record in the cache
                    cache_key = 'id:%s|locator:%s' % (result.id,
                                                      result.locator)
                    cache = self.cache.get_cache('builtin', 'bookings')
                    cache_data = cache.set(
                        cache_key, result.asdict(), details=True)

                    self.response.status_code = OK
                    self.response.payload = cache_data.value
                    self.response.headers['Cache-Control'] = 'no-cache'
                else:
                    self.response.status_code = NOT_FOUND
                    self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraints prevent duplication of bookings via id_guest,
                # id_room and check_in attributes. Also checks that the
                # check-in date is before the check-out date.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class ChangePIN(Service):
    """
    Service class to change the PIN of a booking.

    Channel ``/genesisng/bookings/{id}/pin``.

    Uses `SimpleIO`_.

    Stores the record in the ``bookings`` cache, if found. Returns a
    ``Cache-Control`` header.  Returns a ``Content-Language`` header.

    Returns ``OK`` upon successful modification, or ``NOT_FOUND`` otherwise.
    """
    class SimpleIO:
        input_required = (Integer('id'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'), 'base_price',
                           'taxes_percentage', 'taxes_value', 'total_price',
                           'locator', 'pin', 'status', 'meal_plan',
                           Dict('extras'),
                           # 'uuid' # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights'
                           )

    def handle(self):
        """
        Service handler.

        :param id: The id of the booking.
        :type id: int

        :returns: All attributes of a
            :class:`~genesisng.schema.booking.Booking` model class, including
            the hybrid properties and the newly generated PIN.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_,
                            Booking.deleted.is_(None),
                            Booking.cancelled.is_(None))).\
                one_or_none()

            if result:
                # Generate a new PIN
                result.pin = generate_pin()
                session.commit()

                # Save the record in the cache
                cache_key = 'id:%s|locator:%s' % (result.id, result.locator)
                cache = self.cache.get_cache('builtin', 'bookings')
                cache.set(cache_key, result.asdict())

                # Return the result
                self.response.status_code = OK
                self.response.payload = result
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'


class Validate(Service):
    """
    Service class to validate access to the customer's area of a booking.

    Channel ``/genesisng/bookings/{locator}/validate``.

    Uses `SimpleIO`_.

    Stores the record in the ``bookings`` cache, if found. Returns a
    ``Cache-Control`` header.  Returns a ``Content-Language`` header.

    Returns ``OK`` upon successful modification, or ``FORBIDDEN`` otherwise.
    """
    class SimpleIO:
        input_required = ('locator')
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'), 'base_price',
                           'taxes_percentage', 'taxes_value', 'total_price',
                           'locator', 'pin', 'status', 'meal_plan',
                           Dict('extras'),
                           # 'uuid' # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights'
                           )

    def handle(self):
        """
        Service handler.

        :param locator: The locator of the booking.
        :type locator: str
        :param pin: The PIN of the booking.
        :type pin: str

        :returns: All attributes of a
            :class:`~genesisng.schema.booking.Booking` model class, including
            the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        locator = self.request.input.locator.lower()
        pin = self.request.input.pin

        # Check whether a copy exists in the cache
        cache_key = 'locator:%s' % locator
        cache = self.cache.get_cache('builtin', 'bookings')
        cache_data = cache.get_by_suffix(cache_key, details=True)
        if cache_data and cache_data.value.pin == pin:
            self.response.status_code = OK
            self.response.payload = cache_data.value
            self.response.headers['Cache-Control'] = 'no-cache'
            self.response.headers['Content-Language'] = 'en'
            return

        # Otherwise, retrieve the data
        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.locator == locator,
                            Booking.pin == pin,
                            Booking.deleted.is_(None),
                            Booking.cancelled.is_(None))).\
                one_or_none()

            if result:
                # Save the record in the cache
                cache_key = 'id:%s|locator:%s' % (result.id, result.locator)
                cache_data = cache.set(
                    cache_key, result.asdict(), details=True)

                # Return the result
                self.response.status_code = OK
                self.response.payload = cache_data.value
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'
            else:
                self.response.status_code = FORBIDDEN
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'


class List(Service):
    """
    Service class to get a list of all bookings in the system.

    Channel ``/genesisng/bookings/list``.

    Stores the returned records in the ``bookings`` cache. Returns a
    ``Cache-Control`` header.

    Returns ``NO_CONTENT`` if the returned list is empty, or ``OK`` otherwise.

    Pagination and sorting are always enforced. Filtering is optional. Multiple
    filters are allowed but only one operator for all the filters. Fields
    projection is allowed. Search is not allowed.

    In case of error, it does not return ``BAD_REQUEST`` but, instead, it
    assumes the default parameter values and carries on.

    Includes the count of records returned. It does not return hybrid
    properties.
    """

    criteria_allowed = ('id', 'id_guest', 'id_room', 'check_in', 'check_out')
    direction_allowed = ('asc', 'desc')
    filters_allowed = ('id', 'id_guest', 'id_room', 'reserved', 'guests',
                       'check_in', 'check_out', 'base_price', 'total_price',
                       'status', 'meal_plan', 'extras')
    comparisons_allowed = ('lt', 'lte', 'eq', 'ne', 'gte', 'gt')
    operators_allowed = ('and', 'or')
    fields_allowed = ('id', 'id_guest', 'id_room', 'reserved', 'guests',
                      'check_in', 'check_out', 'checked_in', 'checked_out',
                      'cancelled', 'base_price', 'taxes_percentage',
                      'taxes_value', 'total_price', 'locator', 'pin',
                      'status', 'meal_plan', 'extras', 'uuid',
                      'deleted', 'nights')
    search_allowed = ()

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('fields'), List('operator'))
        # Fields projection makes all output fields optional
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'), 'base_price',
                           'taxes_percentage', 'taxes_value', 'total_price',
                           'locator', 'pin', 'status', 'meal_plan',
                           Dict('extras'),
                           # 'uuid' # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights', 'count'
                           )
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        """
        Service handler.

        Query string parameters:

        :param page: The page number. Default is 1.
        :type page: int
        :param size: The page size. Default is located in the user config.
        :type size: int
        :param sort: The sort criteria (field name) and direction (ascending
            ``asc`` or descending ``desc``), using the pipe ``|`` as separator
            (i.e. ``<criteria>|<direction>``. The default criteria is ``id``
            and the default direction is ``asc``, so the default value of this
            paramter is ``id|asc``.
        :type sort: str
        :param filters: A filter to process the data stream to produce the
            desired output. Each filter is made of a field name, a comparator
            and a value, using the pipe ``|`` as separator (i.e.
            ``<field>|<comparator>|<value>``). Multiple occurrences of this
            parameter are allowed. Supported comparators are ``lt`` (less
            than), ``lte`` (less than or equal), ``eq`` (equal), ``ne`` (not
            equal), ``gte`` (greater than or equal) and ``gt`` (greater than).
        :type filters: str
        :param operator: The operator to apply to or join all filters. The
            supported operators are ``and`` and ``or``. The default value is
            ``and``.
        :type operator: str
        :param fields: Fields projection. A field name of the model class.
            Multiple occurrences of this parameter are allowed. Supported
            fields are all in the :class:`~genesisng.schema.guest.Guest` model
            class.
        :type fields: str

        :returns: A list of dicts with all attributes of a
            :class:`~genesisng.schema.booking.Booking` model class, minus the
            ``days`` hybrid attribute. If fields projection is used, then this
            list will be reduced to the requested fields.
        :rtype: list
        """

        conn = self.user_config.genesisng.database.connection
        default_page_size = int(
            self.user_config.genesisng.pagination.default_page_size)
        max_page_size = int(
            self.user_config.genesisng.pagination.max_page_size)
        cols = Booking.__table__.columns

        # TODO: Have these default values in user config?
        default_criteria = 'id'
        default_direction = 'asc'
        default_operator = 'and'

        # Page number
        try:
            page = int(self.request.input.page[0])
        except (ValueError, KeyError, IndexError):
            page = 1

        # Page size
        try:
            size = int(self.request.input.size[0])
        except (ValueError, KeyError, IndexError):
            size = default_page_size

        # Order by
        try:
            criteria, direction = self.request.input.sort[0].lower().split('|')
        except (ValueError, KeyError, IndexError, AttributeError):
            criteria = default_criteria
            direction = default_direction

        # Filters
        try:
            filters = self.request.input.filters
            operator = self.request.input.operator[0]
        except (ValueError, KeyError, IndexError):
            filters = []
            operator = default_operator

        # Fields projection
        try:
            fields = self.request.input.fields
        except (ValueError, KeyError):
            fields = []

        # Check and adjust parameter values

        # Handle pagination
        page = 1 if page < 1 else page
        size = default_page_size if size < 1 else size
        size = default_page_size if size > max_page_size else size

        # Handle sorting
        if criteria not in self.criteria_allowed:
            criteria = default_criteria
        if direction not in self.direction_allowed:
            direction = default_direction

        # Handle filtering
        conditions = []
        for filter_ in filters:
            field, comparison, value = filter_.split('|')
            if field in self.filters_allowed and \
               comparison in self.comparisons_allowed:
                conditions.append((field, comparison, value))
        if operator not in (self.operators_allowed):
            operator = default_operator

        # Handle fields projection
        columns = []
        for f in fields:
            if f in self.fields_allowed:
                columns.append(f)

        # Compose query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(func.count().over().label('count'))

            # Add columns
            if not columns:
                columns = self.fields_allowed

            for c in columns:
                query = query.add_columns(cols[c])

            # Prepare filters
            # TODO: Use sqlalchemy-filters?
            # https://pypi.org/project/sqlalchemy-filters/
            if conditions:
                clauses = []
                for c in conditions:
                    f, o, v = c
                    if o == 'lt':
                        clauses.append(cols[f] < v)
                    elif o == 'lte':
                        clauses.append(cols[f] <= v)
                    elif o == 'eq':
                        clauses.append(cols[f] == v)
                    elif o == 'ne':
                        clauses.append(cols[f] != v)
                    elif o == 'gte':
                        clauses.append(cols[f] >= v)
                    elif o == 'gt':
                        clauses.append(cols[f] > v)
                if operator == 'or':
                    query = query.filter(or_(*clauses))
                else:
                    query = query.filter(and_(*clauses))

            # Order by
            if direction == 'asc':
                query = query.order_by(cols[criteria].asc())
            else:
                query = query.order_by(cols[criteria].desc())

            # Calculate limit and offset
            limit = size
            offset = size * (page - 1)
            query = query.offset(offset)
            query = query.limit(limit)

            # Execute query
            result = query.all()

            # Return result
            if result:

                # Store results in the cache only if all fields were retrieved
                if not fields:
                    cache = self.cache.get_cache('builtin', 'bookings')
                    for r in result:
                        # Items are already dictionaries.
                        cache_key = 'id:%s|locator:%s' % (r.id, r.locator)
                        cache.set(cache_key, r)

                self.response.status_code = OK
                self.response.payload[:] = result
                self.response.headers['Cache-Control'] = 'no-cache'
            else:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'


class Restore(Service):
    """
    Service class to restore a deleted booking.

    Channel ``/genesisng/bookingss/{id}/restore``.

    Uses `SimpleIO`_.

    Stores the record in the ``bookings`` cache. Returns ``Cache-Control``,
    ``Last-Modified`` and ``ETag`` headers. Returns a ``Content-Language``
    header.

    Returns ``OK`` upon successful retrieval, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        output_optional = ('id', 'id_guest', 'id_room', DateTime('reserved'),
                           'guests', Date('check_in'), Date('check_out'),
                           DateTime('checked_in'), DateTime('checked_out'),
                           DateTime('cancelled'), 'base_price',
                           'taxes_percentage', 'taxes_value', 'total_price',
                           'locator', 'pin', 'status', 'meal_plan',
                           Dict('extras'),
                           # 'uuid' # JSON serializaction error
                           # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                           'nights'
                           )
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the booking.
        :type id: int

        :returns: All attributes of a
            :class:`~genesisng.schema.booking.Booking` model class, including
            the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Booking).\
                filter(and_(Booking.id == id_, Booking.deleted.isnot(None))).\
                one_or_none()

            if result:
                # Update dictionary key
                result.deleted = None
                session.commit()

                # Save the record in the cache
                cache_key = 'id:%s|locator:%s' % (result.id, result.locator)
                cache = self.cache.get_cache('builtin', 'bookings')
                cache.set(cache_key, result.asdict())

                # Return the result
                self.response.status_code = OK
                self.response.payload = result
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'
