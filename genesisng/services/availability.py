# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, BAD_REQUEST, CREATED, CONFLICT
from zato.server.service import Service
from zato.server.service import Integer, Date, List, Dict, AsIs
from genesisng.schema.room import Room
from genesisng.schema.rate import Rate
from genesisng.schema.booking import Booking
from genesisng.schema.extra import Extra
from sqlalchemy import func, tuple_, case, cast, any_
from sqlalchemy import Integer as sqlInteger
from sqlalchemy import Float as sqlFloat
from sqlalchemy import Date as sqlDate
from uuid import UUID
from datetime import datetime
from math import ceil


class Search(Service):
    """
    Service class to search for availability.

    Channel ``/genesisng/availability/search``.

    Uses `SimpleIO`_.

    Stores the search results in the ``availability`` cache. Returns
    ``Cache-Control``, ``Last-Modified`` and ``ETag`` headers. Returns a
    ``Content-Language`` header.

    Returns ``OK`` if results have been found, ``NO_CONTENT`` if there is no
    availability or ``BAD_REQUEST`` if the check-in date is not before the
    check-out date and there is at least 1 day in between.
    """

    class SimpleIO(object):
        input_required = (Date('check_in'), Date('check_out'),
                          Integer('guests'))
        input_optional = (List('rooms'), AsIs('session'))
        output_optional = ('id', 'number', 'name', 'sgl_beds', 'dbl_beds',
                           'accommodates', 'code', 'nights', 'price',
                           'taxes_percentage', 'taxes_value', 'total_price')
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        """
        Service handler.

        :param guests: The number of guests
        :type guests: int
        :param check_in: The date the guests want to arrive.
        :type check_in: date
        :param check_out: The date the guests want to leave.
        :type check_out: date
        :param rooms: A list of room ids to filter the results
        :type rooms: list
        :param session: A live session (transaction) to be reused. Optional.
        :type session: :class:`~sqlalchemy.orm.session.Session`

        :returns: A sub-set of :class:`~genesisng.schema.room.Room` properties,
            the number of nights and the pricing details of the booking.
        :rtype: list of dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        taxes_percentage = self.user_config.genesisng.availability.taxes_percentage
        check_in = self.request.input.check_in
        check_out = self.request.input.check_out
        guests = self.request.input.guests

        check_in = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out, '%Y-%m-%d').date()

        # Check dates
        if check_in >= check_out:
            self.response.status_code = BAD_REQUEST
            msg = 'Check-in date must be at least 1 day before check-out date.'
            self.response.payload = {'error': {'message': msg}}
            return

        # Process optional list of room ids
        try:
            rooms = list(map(
                int,
                self.request.input.rooms)) if self.request.input.rooms else []
        except ValueError:
            rooms = []

        # Check whether a copy exists in the cache
        cache_key = 'check_in:%s|check_out:%s|guests:%s|rooms:%s' % (
            check_in.strftime('%Y-%m-%d'), check_out.strftime('%Y-%m-%d'),
            guests, str(rooms))
        cache = self.cache.get_cache('builtin', 'availability')
        cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.headers['Content-Language'] = 'en'
            self.response.payload[:] = cache_data.value
            return

        # Reuse the session if any has been provided
        if self.request.input.session:
            session = self.request.input.session
        else:
            session = self.outgoing.sql.get(conn).session()

        # Sum of nights and prices per season (0..N)
        p = session.query(
            func.SUM(
                case(
                    [(check_out > Rate.date_to, Rate.date_to)],
                    else_=check_out
                ) -
                case(
                    [(check_in > Rate.date_from, check_in)],
                    else_=Rate.date_from
                )
                ).label('nights'),
            (func.SUM((
                case(
                    [(check_out > Rate.date_to, Rate.date_to)],
                    else_=check_out
                ) -
                case(
                    [(check_in > Rate.date_from, check_in)],
                    else_=Rate.date_from
                )) * (Rate.base_price + Rate.bed_price * guests)
                ).label('price'))
            ).\
            filter(
                tuple_(Rate.date_from, Rate.date_to).
                op('OVERLAPS')
                (tuple_(cast(check_in, sqlDate), cast(check_out, sqlDate)))
            ).\
            filter(Rate.published.is_(True)).\
            cte(name='p')

        # Room availability using a sub-select
        subq = session.query(Booking.id_room.label('id')).\
            filter(
                tuple_(Booking.check_in, Booking.check_out).
                op('OVERLAPS')
                (tuple_(cast(check_in, sqlDate), cast(check_out, sqlDate)))
            ).\
            filter(Booking.cancelled.is_(None)).\
            subquery('subq')

        a = session.query(Room.id, Room.floor_no, Room.room_no, Room.name,
                          Room.sgl_beds, Room.dbl_beds,  Room.supplement,
                          Room.code, Room.number, Room.accommodates).\
            filter(Room.deleted.is_(None)).\
            filter(Room.id.notin_(subq)).\
            filter(Room.accommodates >= guests)
        if rooms:
            a = a.filter(Room.id == any_(rooms))
        a = a.cte(name='a')

        # Execute query
        total_price = a.c.supplement * p.c.nights + p.c.price
        result = session.query(
            a.c.id, a.c.floor_no, a.c.room_no, a.c.name, a.c.sgl_beds,
            a.c.dbl_beds, a.c.code, a.c.number, a.c.accommodates,
            cast(p.c.nights, sqlInteger).label('nights'),
            cast(p.c.price, sqlFloat).label('price')).\
            order_by(total_price.asc()).\
            order_by(a.c.accommodates.asc()).\
            order_by(a.c.sgl_beds.asc()).\
            order_by(a.c.dbl_beds.asc()).\
            order_by(a.c.floor_no.asc()).\
            order_by(a.c.room_no.asc()).\
            all()

        if result:
            # A complex result set cannot be stored in the cache as list of
            # WritableKeyedTuple, so we transform it into a list of
            # dictionaries.
            lod = []
            for r in result:
                # To prevent missing decimals, taxes amount is rounded
                # down/up using math.ceil()
                taxes_value = ceil(r.price * taxes_percentage / 100)
                d = {
                    'id': r.id,
                    'number': r.number,
                    'name': r.name,
                    'sgl_beds': r.sgl_beds,
                    'dbl_beds': r.dbl_beds,
                    'accommodates': r.accommodates,
                    'code': r.code,
                    'nights': r.nights,
                    'price': r.price,
                    'taxes_percentage': taxes_percentage,
                    'taxes_value': taxes_value,
                    'total_price': r.price + taxes_value
                }
                lod.append(d)

            # Store results in the cache
            cache_data = cache.set(cache_key, lod, details=True)

            if cache_data:
                self.response.headers['Cache-Control'] = cache_control
                self.response.headers['Last-Modified'] = cache_data.\
                    last_write_http
                self.response.headers['ETag'] = cache_data.hash
            else:
                self.response.headers['Cache-Control'] = 'no-cache'

            # Return the result
            self.response.payload[:] = lod
            self.response.status_code = OK
        else:
            self.response.status_code = NO_CONTENT
            self.response.headers['Cache-Control'] = 'no-cache'

        # Close the session only if we created a new one
        if not self.request.input.session:
            session.close()


class Extras(Service):
    """
    Service class to get a list of available extras for a room.

    Channel ``/genesisng/availability/extras``.

    Uses `SimpleIO`_.

    Stores the list of extras in the ``availability`` cache. Returns
    ``Cache-Control``, ``Last-Modified`` and ``ETag`` headers. Returns a
    ``Content-Language`` header.

    Returns ``OK`` if results have been found, ``NO_CONTENT`` if there are no
    available extras for the room.
    """

    class SimpleIO(object):
        input_optional = (AsIs('session'))
        output_optional = ('id', 'code', 'name', 'description', 'price')
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        """
        Service handler.

        :param session: A live session (transaction) to be reused. Optional.
        :type session: :class:`~sqlalchemy.orm.session.Session`

        :returns: All available extras, each including all attributes of a
            :class:`~genesisng.schema.rate.Rate` model class.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control

        # Check whether a copy exists in the cache
        cache_key = 'extras'
        cache = self.cache.get_cache('builtin', 'availability')
        cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.headers['Content-Language'] = 'en'
            self.response.payload[:] = cache_data.value
            return

        # Reuse the session if any has been provided
        if self.request.input.session:
            session = self.request.input.session
        else:
            session = self.outgoing.sql.get(conn).session()

        # Get the list of extras
        result = session.query(Extra).filter(Extra.deleted.is_(None)).all()

        if result:

            # Transform the result (a list of Extra objects) into a list of
            # dictionaries so that they can be stored in the cache.
            lod = [r.asdict() for r in result]

            # Save the record in the cache
            cache_data = cache.set(cache_key, lod, details=True)

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
            self.response.payload[:] = lod
            self.response.headers['Content-Language'] = 'en'
        else:
            self.response.status_code = NO_CONTENT
            self.response.headers['Cache-Control'] = 'no-cache'
            self.response.headers['Content-Language'] = 'en'

        # Close the session only if we created a new one
        if not self.request.input.session:
            session.close()


class Confirm(Service):
    """
    Service class to make a reservation.

    Channel ``/genesisng/availability/confirm``.

    Uses `SimpleIO`_.

    Creates the guest, or updates an existing one if the email already exists,
    and a booking.

    Publishes a message to the ``/genesisng/bookings`` topic name.

    Invalidates the affected portion of the ``availability`` cache collection,
    if possible, or the whole collection otherwise.

    Returns ``CREATED`` if the new reservation was successfully created and the
    associated client was successfully created or updated, ``BAD_REQUEST`` if
    an issue was found with the input parameters and ``CONFLICT`` if the
    reservation could not be made due to lack of availability.

    Invokes the services :class:`~genesisng.services.guest.Upsert`,
    :class:`~genesisng.services.booking.Create`,
    :class:`~genesisng.services.availability.Extras`,
    :class:`~genesisng.services.availability.Search` and
    :class:`~genesisng.services.room.Get` to retrieve the required data.
    """

    class SimpleIO(object):
        input_required = (
            Integer('guests'), Date('check_in'), Date('check_out'),
            Integer('id_room'), 'uuid', 'name', 'surname', 'email')
        input_optional = (
            'status', 'meal_plan', List('extras', default=[]), 'gender',
            'passport', Date('birthdate'), 'address1', 'address2', 'locality',
            'postcode', 'province', 'country', 'home_phone', 'mobile_phone')
        output_optional = (
            Dict('booking',
                 # 'id', 'id_guest', 'id_room', DateTime('reserved'),
                 # 'guests', Date('check_in'), Date('check_out'),
                 # DateTime('checked_in'), DateTime('checked_out'),
                 # DateTime('cancelled'), 'base_price', 'taxes_percentage',
                 # 'taxes_value', 'total_price', 'locator', 'pin', 'status',
                 # 'meal_plan', Dict('extras'),
                 # 'uuid' # JSON serializaction error
                 # https://forum.zato.io/t/returning-uuid-types-from-services-using-json/1735
                 # 'nights'
                 ),
            Dict('guest',
                 # 'id',  'name', 'surname', 'gender', 'email', 'passport',
                 # Date('birthdate'), 'address1', 'address2', 'locality',
                 # 'postcode', 'province', 'country', 'home_phone',
                 # 'mobile_phone'
                 ),
            Dict('room',
                 # 'id', 'floor_no', 'room_no', 'sgl_beds', 'dbl_beds',
                 # 'supplement', 'code', 'name', 'accommodates', 'number'
                 ),
            Dict('error')
            )
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param guests: The number of guests in the reservation.
        :type guests: int
        :param check_in: The date the guests want to arrive.
        :type check_in: date
        :param check_out: The date the guests want to leave.
        :type check_out: date
        :param id_room: A room id that will be associated to the booking.
        :type id_room: int
        :param total_price: The total price of the reservation, excluding
            extras or meal plan.
        :type total_price: float
        :param status: The booking status. Optional. Defaults to 'New'.
        :type status: enum
        :param meal_plan: The meal plan for the booking. Optional. Defaults to
            'BedAndBreakfast'.
        :type meal_plan: enum
        :param extras: The list of selected extras. Optional. Defaults to an
            empty string, i.e. no extras.
        :type extras: list
        :param uuid: The UUIDv4 generated by the client to uniquely identify
            this request and prevent duplicated bookings.
        :type uuid: str
        :param name: The first name of the guest.
        :type name: str
        :param surname: The last name of the guest.
        :type surname: str
        :param gender: The gender of the guest. Optional. Defaults to 'Male'.
        :type gender: enum
        :param email: The electronic mail address of the guest.
        :type email: str
        :param passport: The passport number, tax id or similar identification
            number.
        :type passport: str
        :param address1: The postal address of the guest.
        :type address1: str
        :param address2: Additional information of the postal address.
        :type address2: str
        :param locality: The city, town or similar.
        :type locality: str
        :param postcode: The postal code.
        :type postcode: str
        :param province: The province, county, state or similar.
        :type province: str
        :param home_phone: The home phone number.
        :type home_phone: str
        :param mobile_phone: The mobile phone number.
        :type mobile_phone: str

        :returns: A dictionary with all available attributes of a
            :class:`~genesisng.schema.booking.Booking`, a
            :class:`~genesisng.schema.room.Room` and of a
            :class:`~genesisng.schema.guest.Guest` in separate keys.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        taxes_percentage = self.user_config.genesisng.availability.taxes_percentage
        p = self.request.input

        try:
            check_in = datetime.strptime(p.check_in, '%Y-%m-%d').date()
            check_out = datetime.strptime(p.check_out, '%Y-%m-%d').date()
        except ValueError:
            self.response.status_code = BAD_REQUEST
            msg = 'Wrong check-in or check-out date format.'
            self.response.payload = {'error': {'message': msg}}
            return

        # Check dates
        if check_in >= check_out:
            self.response.status_code = BAD_REQUEST
            msg = 'Check-in date must be before check-out date.'
            self.response.payload = {'error': {'message': msg}}
            return

        # Check UUID string and convert it into an actual UUID
        try:
            uuid = UUID(p.uuid, version=4)
        except ValueError:
            self.response.status_code = BAD_REQUEST
            msg = 'Wrong UUID version 4 format.'
            self.response.payload = {'error': {'message': msg}}
            return

        # Process optional list of extra ids
        try:
            loe = list(map(int, p.extras)) if p.extras else []
        except ValueError:
            self.response.status_code = BAD_REQUEST
            msg = 'The list of passed extras has non-integer values.'
            self.response.payload = {'error': {'message': msg}}
            return

        try:
            if p.birthdate:
                datetime.strptime(p.birthdate, '%Y-%m-%d').date()
        except ValueError:
            self.response.status_code = BAD_REQUEST
            msg = 'Wrong birthdate format.'
            self.response.payload = {'error': {'message': msg}}
            return

        with closing(self.outgoing.sql.get(conn).session()) as session:

            # Prepare extras to be saved by turning a list of integers into a
            # dictionary with code, name, description and price.
            extras = {'list': []}
            if loe:
                input_data = {'session': session}
                all_extras = self.invoke('availability.extras', input_data,
                                         as_bunch=True)
                for extra in all_extras['response']:
                    if extra.id in loe:
                        extras['list'].append({
                            'code': extra.code,
                            'name': extra.name,
                            'description': extra.description,
                            'price': extra.price
                        })

            # Check for availability and get pricing information
            input_data = {
                'check_in': p.check_in,
                'check_out': p.check_out,
                'guests': p.guests,
                'rooms': [p.id_room],
                'session': session
            }
            availability = self.invoke('availability.search', input_data,
                                       as_bunch=True)
            if availability['response']:
                res = availability['response'][0]
                price = res.price
                taxes_percentage = res.taxes_percentage
                taxes_value = res.taxes_value
                total_price = res.total_price
            else:
                self.response.status_code = CONFLICT
                msg = 'There is no availability for the requested dates, number of guests and room.'
                self.response.payload = {'error': {'message': msg}}
                return

            # Save new records on the database and prepare the result to be
            # returned.
            result = {}

            # Save the guest and add it to the result
            input_data = {
                'name': p.name,
                'surname': p.surname,
                'gender': p.gender,
                'email': p.email,
                'passport': p.passport,
                'birthdate': p.birthdate,
                'address1': p.address1,
                'address2': p.address2,
                'locality': p.locality,
                'postcode': p.postcode,
                'province': p.province,
                'country': p.country,
                'home_phone': p.home_phone,
                'mobile_phone': p.mobile_phone,
                'session': session
            }
            # Remove empty strings from input data
            for k in input_data.keys():
                if input_data[k] == '':
                    del (input_data[k])
            guest = self.invoke('guest.upsert', input_data, as_bunch=True)
            if guest['response']:
                result['guest'] = guest['response']
            else:
                self.response.status_code = CONFLICT
                msg = 'Could not create guest.'
                self.response.payload = {'error': {'message': msg}}
                return

            # Save the booking and add it to the result
            input_data = {
                'id_guest': guest['response'].id,
                'id_room': p.id_room,
                'guests': p.guests,
                'check_in': p.check_in,
                'check_out': p.check_out,
                'base_price': price,
                'taxes_percentage': taxes_percentage,
                'taxes_value': taxes_value,
                'total_price': total_price,
                'status': p.status,
                'meal_plan': p.meal_plan,
                'extras': extras,
                'uuid': uuid,
                'session': session
            }
            # Remove empty strings from input data
            for k in input_data.keys():
                if input_data[k] == '':
                    del (input_data[k])
            booking = self.invoke('booking.create', input_data, as_bunch=True)
            if booking['response']:
                result['booking'] = booking['response']
            self.logger.info('Booking response is: %s' % booking['response'])

            # Get room information and add it to the result
            input_data = {'id': p.id_room, 'session': session}
            room = self.invoke('room.get', input_data)
            if room['response']:
                result['room'] = room['response']

            if result:

                # Invalidate the ``availability`` cache.
                # TODO: Invalidate the affected portion only (i.e. entries
                # whose dates overlap for the same room id.
                self.logger.debug('Clearing availability cache')
                cache = self.cache.get_cache('builtin', 'availability')
                cache.clear()

                # Publish a message to ``/genesisng/bookings`` topic name.
                topic_name = '/genesisng/bookings'
                data = 'booking-new:%s' % booking['response'].id
                self.logger.info(
                    'Publishing message to queue %s for a new booking with id %s' % (
                        topic_name, booking['response'].id))
                msg_id = self.pubsub.publish(topic_name, data=data,
                                             has_gd=True, priority=5)
                self.logger.info('Message id is %s' % msg_id)

                # Return the result
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.status_code = CREATED
                self.response.payload = result
                self.response.headers['Content-Language'] = 'en'
            else:
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.status_code = CONFLICT
                msg = 'Could not confirm availability for the given parameters'
                self.response.payload = {'error': {'message': msg}}

            # Commit the transaction
            session.commit()
