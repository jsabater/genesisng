# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from contextlib import closing
from httplib import OK, NO_CONTENT, BAD_REQUEST
from zato.server.service import Service
from zato.server.service import Integer, Date, List
from genesisng.schema.room import Room
from genesisng.schema.rate import Rate
from genesisng.schema.booking import Booking
from sqlalchemy import func, tuple_, case, cast, any_
from sqlalchemy import Integer as sqlInteger
from sqlalchemy import Float as sqlFloat
from sqlalchemy import Date as sqlDate
from datetime import datetime


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
        input_optional = (List('rooms'))
        output_optional = ('id', 'number', 'name', 'sbl_beds', 'dbl_beds',
                           'accommodates', 'code', 'nights', 'total_price')
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

        :returns: All attributes of a
            :class:`~genesisng.schema.availability.Result` model class.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        check_in = self.request.input.check_in
        check_out = self.request.input.check_out
        guests = self.request.input.guests

        check_in = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out, '%Y-%m-%d').date()

        # Check dates
        if check_in >= check_out:
            self.response.status_code = BAD_REQUEST
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
            self.response.payload = cache_data.value
            return

        # Otherwise, retrieve the data
        with closing(self.outgoing.sql.get(conn).session()) as session:

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
                cast(total_price, sqlFloat).label('total_price')).\
                order_by(total_price.asc()).\
                order_by(a.c.accommodates.asc()).\
                order_by(a.c.sgl_beds.asc()).\
                order_by(a.c.dbl_beds.asc()).\
                order_by(a.c.floor_no.asc()).\
                order_by(a.c.room_no.asc()).\
                all()

            if result:
                # A complex result set cannot be stored in the cache (a list of
                # WritableKeyedTuple in this case), so we transform it into a
                # list of dictionaries
                lod = []
                for r in result:
                    d = {
                        'id': r.id,
                        'number': r.number,
                        'name': r.name,
                        'sbl_beds': r.sgl_beds,
                        'dbl_beds': r.dbl_beds,
                        'accommodates': r.accommodates,
                        'code': r.code,
                        'nights': r.nights,
                        'total_price': r.total_price
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
        output_optional = ('id', 'code', 'name', 'description', 'price')
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        """
        Service handler.

        :returns: All available extras.
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
            self.response.payload = cache_data.value
            return

        # Otherwise, retrieve the data
        with closing(self.outgoing.sql.get(conn).session()) as session:

            # result = session.query(Extra).filter(Extra.deleted.is_(None)).all()

            result = [
                {
                    'id': 1,
                    'code': 'LateDinner',
                    'name': 'Dinner for late arrivals',
                    'description': 'Find a cold dinner in your room when arriving later than 22:00 h.',
                    'price': 0
                },
                {
                    'id': 2,
                    'code': 'PoolKit',
                    'name': 'Swimming pool kit',
                    'description': 'Bathrobe and slippers to wear in the hotel',
                    'price': 0
                },
                {
                    'id': 3,
                    'code': 'Massage30',
                    'name': '30 minutes massage',
                    'description': 'To help you relax or recover from physical exercise',
                    'price': 0
                }
            ]

            if result:
                # Save the record in the cache
                cache_data = cache.set(cache_key, result, details=True)

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
                self.response.payload[:] = result
                self.response.headers['Content-Language'] = 'en'
            else:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'