# -*- coding: utf-8 -*-
from contextlib import closing
from http.client import OK, NO_CONTENT, CREATED, NOT_FOUND, CONFLICT
from bunch import Bunch
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from zato.server.service import Service, Integer, Float, Date, Boolean, List
from genesisng.schema.rate import Rate
from genesisng.util.config import parse_args
from genesisng.util.filters import parse_filters


class Get(Service):
    """
    Service class to get a rate by id.

    Channel ``/genesisng/rates/{id}/get``.

    Uses `SimpleIO`_.

    Stores the record in the ``guests`` cache. Returns ``Cache-Control``,
    ``Last-Modified`` and ``ETag`` headers.  Returns a ``Content-Language``
    header.

    Returns ``OK`` upon successful retrieval, or ``NOT_FOUND`` otherwise.
    """

    class SimpleIO(object):
        input_required = (Integer('id'))
        output_optional = ('id', 'date_from', 'date_to', 'base_price',
                           'bed_price', 'published', 'days')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the rate.
        :type id: int

        :returns: All attributes of a :class:`~genesisng.schema.rate.Rate`
            model class, including the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control
        id_ = self.request.input.id

        # Check whether a copy exists in the cache
        cache_key = 'id-%s' % id_
        cache = self.cache.get_cache('builtin', 'rates')
        cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.headers['Content-Language'] = 'en'
            self.response.payload = cache_data.value
            return

        with closing(self.outgoing.sql.get(conn).session()) as session:
            result = session.query(Rate).\
                filter(and_(Rate.id == id_, Rate.published.is_(True))).\
                one_or_none()

            if result:
                # Save the record in the cache
                cache_data = cache.set(
                    cache_key, result.asdict(), details=True)

                # Return the result
                self.response.status_code = OK
                self.response.headers['Cache-Control'] = cache_control
                self.response.headers['Last-Modified'] = cache_data.\
                    last_write_http
                self.response.headers['ETag'] = cache_data.hash
                self.response.headers['Content-Language'] = 'en'
                self.response.payload = result
            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'
                self.response.headers['Content-Language'] = 'en'


class Create(Service):
    """
    Service class to create a new rate.

    Channel /genesisng/rates/create.

    Uses `SimpleIO`_.

    Stores the record in the ``rates`` cache. Returns a ``Cache-Control``
    header.

    Returns ``CREATED`` upon successful creation, or ``CONFLICT`` otherwise.
    """

    class SimpleIO:
        input_required = (Date('date_from'), Date('date_to'),
                          Float('base_price'), Float('bed_price'))
        input_optional = (Boolean('published', default=False))
        output_optional = ('id', 'date_from', 'date_to', 'base_price',
                           'bed_price', 'published', 'days')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param date_from: The start date of the period of time covered.
        :type date_from: date
        :param date_to: The end date of the period of time covered.
        :type date_to: date
        :param base_price: The base startingprice of this rate, on top of which
            calculations are made. Default is 0.
        :type base_price: float
        :param bed_price: The price per bed to be added to the base price.
            Default is 0.
        :type bed_price: float
        :param published: Is this rate active? Defaults to False.
        :type published: bool

        :returns: All attributes of a :class:`~genesisng.schema.rate.Rate`
            model class, including the hybrid properties.
        :rtype: dict
        """

        # TODO: Use Cerberus to validate input?
        # http://docs.python-cerberus.org/en/stable/
        conn = self.user_config.genesisng.database.connection

        p = self.request.input
        result = Rate(
            date_from=p.date_from,
            date_to=p.date_to,
            base_price=p.get('base_price', 0),
            bed_price=p.get('bed_price', 0),
            published=p.get('published', False))

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                session.add(result)
                session.commit()

                # Save the record in the cache
                cache_key = 'id-%s' % result.id
                cache = self.cache.get_cache('builtin', 'rates')
                result = result.asdict()
                cache.set(cache_key, result)

                # Return the result
                self.response.status_code = CREATED
                self.response.payload = result
                url = self.user_config.genesisng.location.rates
                self.response.headers['Location'] = url.format(id=result.id)
                self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraint prevents overlapping dates.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'
                # TODO: Return well-formed error response?
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948
                # TODO: Handle duplicated codes (retry with another code).


class Delete(Service):
    """
    Service class to delete an existing rate.

    Channel ``/genesisng/rates/{id}/delete``.

    Uses `SimpleIO`_.

    Removes the record from the ``rates`` cache, if found. Returns a
    ``Cache-Control`` header.

    Returns ``NO_CONTENT`` upon successful deletion, or ``NOT_FOUND``
    therwise.
    """

    class SimpleIO:
        input_required = (Integer('id'))

    def handle(self):
        """
        Service handler.

        :param id: The id of the rate.
        :type id: int

        :returns: Nothing.
        """
        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id

        with closing(self.outgoing.sql.get(conn).session()) as session:
            deleted = session.query(Rate).filter(Rate.id == id_).delete()
            session.commit()

            if deleted:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'

                # Invalidate the cache
                cache_key = 'id-%s' % id_
                cache = self.cache.get_cache('builtin', 'rates')
                cache.delete(cache_key)

            else:
                self.response.status_code = NOT_FOUND
                self.response.headers['Cache-Control'] = 'no-cache'


class Update(Service):
    """
    Service class to update an existing rate.

    Channel ``/genesisng/rates/{id}/update``.

    Uses `SimpleIO`_.

    Stores the updated record in the ``rates`` cache. Returns a
    ``Cache-Control`` header. Only non-empty keys will be updated.

    Returns ``OK`` upon successful modification, ``NOT_FOUND`` if the record
    cannot be found, or ``CONFLICT`` in case of a constraint error.

    Attributes not sent through the request are not updated.
    """

    class SimpleIO:
        input_required = (Integer('id'))
        input_optional = (Date('date_from'), Date('date_to'),
                          Float('base_price'), Float('bed_price'),
                          Boolean('published', default=False))
        output_optional = ('id', 'date_from', 'date_to', 'base_price',
                           'bed_price', 'published', 'days')
        skip_empty_keys = True

    def handle(self):
        """
        Service handler.

        :param id: The id of the rate. Mandatory.
        :type id: int
        :param date_from: The start date of the period of time covered.
        :type date_from: date
        :param date_to: The end date of the period of time covered.
        :type date_to: date
        :param base_price: The base startingprice of this rate, on top of which
            calculations are made. Default is 0.
        :type base_price: float
        :param bed_price: The price per bed to be added to the base price.
            Default is 0.
        :type bed_price: float
        :param published: Is this rate active? Defaults to False.
        :type published: bool

        :returns: All attributes of a :class:`~genesisng.schema.rate.Rate`
            model class, including the hybrid properties.
        :rtype: dict
        """

        conn = self.user_config.genesisng.database.connection
        id_ = self.request.input.id
        p = self.request.input

        with closing(self.outgoing.sql.get(conn).session()) as session:
            try:
                result = session.query(Rate).filter(Rate.id == id_).\
                         one_or_none()

                if result:
                    # TODO: Implement a wrapper to remove empty request keys,
                    # or add request params to skip_empty_keys as per
                    # https://forum.zato.io/t/leave-the-simpleio-input-optional-out-of-the-input/593/22
                    # then use dictalchemy's .fromdict() to reduce code.
                    # result.fromdict(self.request.input, allow_pk=True)

                    # Update dictionary keys
                    if p.date_from:
                        result.date_from = p.date_from
                    if p.date_to:
                        result.date_to = p.date_to
                    if p.base_price:
                        result.base_price = p.base_price
                    if p.bed_price:
                        result.bed_price = p.bed_price
                    if p.published != '':
                        result.published = p.published
                    session.commit()

                    # Save the record in the cache
                    cache_key = 'id-%s' % result.id
                    cache = self.cache.get_cache('builtin', 'rates')
                    cache_data = cache.set(
                        cache_key, result.asdict(), details=True)

                    # Return the result
                    self.response.status_code = OK
                    self.response.payload = cache_data.value
                    self.response.headers['Cache-Control'] = 'no-cache'
                else:
                    self.response.status_code = NOT_FOUND
                    self.response.headers['Cache-Control'] = 'no-cache'

            except IntegrityError:
                # Constraint prevents overlapping of dates and makes sure that
                # date_from is always before date_to.
                session.rollback()
                self.response.status_code = CONFLICT
                self.response.headers['Cache-Control'] = 'no-cache'
                # TODO: Return well-formed error response
                # https://medium.com/@suhas_chatekar/return-well-formed-error-responses-from-your-rest-apis-956b5275948


class List(Service):
    """
    Service class to get a list of all rates in the system.

    Channel ``/genesisng/rates/list``.

    Uses `SimpleIO`_.

    Stores every retrieved row as a cache item in the ``rates`` cache
    collection, which will be later used in the ``Get`` service. Returns a
    ``Cache-Control`` header.

    Returns ``NO_CONTENT`` if the returned list is empty, or ``OK`` otherwise.

    Pagination and sorting are always enforced. Filtering is optional. Multiple
    filters are allowed but only one operator for all the filters. Fields
    projection is not allowed. Search is not allowed.

    In case of error, it does not return ``BAD_REQUEST`` but, instead, it
    assumes the default parameter values and carries on.

    The page number (``X-Genesis-Page``) and the page size (``X-Genesis-Size``)
    are returned as headers. It does not include the total count of records
    (``X-Genesis-Count``), as one is expected to always filter by seasons (i.e.
    years). This context also serves to demonstrate the difference between
    using the entity (i.e. :class:`~genesisng.schema.rate.Rate`) or the entity
    columns in the query.
    """

    # Fields allowed in sorting criteria, filters, field projection or
    # searched in.
    allowed = Bunch({
        'criteria': ('id', 'date_from', 'date_to', 'base_price', 'bed_price'),
        'filters': ('id', 'date_from', 'date_to', 'base_price', 'bed_price'),
        'fields': (),
        'search': ()
    })

    class SimpleIO:
        input_optional = (List('page'), List('size'), List('sort'),
                          List('filters'), List('operator'))
        output_optional = ('id', Date('date_from'), Date('date_to'),
                           'base_price', 'bed_price', 'published', 'days')
        output_repeated = True
        skip_empty_keys = True

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

        :returns: A list of dicts with all attributes of a
            :class:`~genesisng.schema.rate.Rate` model class, including the
            ``days`` hybrid attribute.
        :rtype: list
        """

        # Shortcut to the entity columns
        cols = Rate.__table__.columns

        # Database connection
        conn = self.user_config.genesisng.database.connection

        # Parse received arguments
        params = parse_args(self.request.input, self.allowed,
                            self.user_config.genesisng.pagination, self.logger)

        # Compose query
        with closing(self.outgoing.sql.get(conn).session()) as session:
            query = session.query(Rate)

            # Prepare filters
            query = parse_filters(params.filters, params.operator, cols, query)

            # Search: add ilike clauses if there is a search term.
            if params.search:
                clauses = []
                for s in self.paging.search:
                    clauses.append(cols[s].ilike(params.search))
                query = query.filter(or_(*clauses))

            # Order by
            if params.direction == 'asc':
                query = query.order_by(cols[params.criteria].asc())
            else:
                query = query.order_by(cols[params.criteria].desc())

            # Add limit and offset
            query = query.offset(params.offset)
            query = query.limit(params.limit)

            # Execute query
            result = query.all()

            # Return now if no rows were returned
            if not result:
                self.response.status_code = NO_CONTENT
                self.response.headers['Cache-Control'] = 'no-cache'
                return

            # Get cache collection
            try:
                cache = self.cache.get_cache('builtin', 'rates')
            except Exception:
                self.logger.error(
                    "Could not get the 'rates' cache collection.")

            # Loop the result set
            for r in result:
                # Store each row (a WritableKeyedTuple) in the cache as a dict
                if cache is not None:
                    cache.set('id:%s' % r.id, r._asdict())

            # Return the result set
            self.response.payload[:] = result
            self.response.status_code = OK
            self.response.headers['Cache-Control'] = 'no-cache'
            self.response.headers['Content-Language'] = 'en'
            self.response.headers['X-Genesis-Page'] = str(params.page)
            self.response.headers['X-Genesis-Size'] = str(params.size)
