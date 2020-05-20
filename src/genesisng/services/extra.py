# -*- coding: utf-8 -*-
from http.client import OK, NO_CONTENT
from zato.server.service import Service
from genesisng.schema.extra import Extra


class List(Service):
    """
    Service class to get the list of available extras for all rooms.

    Channel ``/genesisng/extras/list``.

    Uses `SimpleIO`_.

    Stores the list of extras in the ``availability`` cache. Returns
    ``Cache-Control``, ``Last-Modified`` and ``ETag`` headers. Returns a
    ``Content-Language`` header.

    Returns ``NO_CONTENT`` if the returned list is empty, or ``OK`` otherwise.

    Sorting is always enforced. Filtering, fields projection, search and
    pagination are not allowed.

    Sorting is always enforced. Filtering, fields projection, search and
    pagination are not allowed. Given that the result set will always be small,
    filtering is expected to be done in the controller class or in the client.

    In case of error, it does not return ``BAD_REQUEST`` but, instead, it
    assumes the default parameter values and carries on.

    This service is invoked from other services (e.g. availability.confirm), so
    the database session is reused when possible so that all queries are kept
    inside the same transaction. Also, environment variables
    """

    class SimpleIO(object):
        output_optional = ('id', 'code', 'name', 'description', 'price')
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        """
        Service handler.

        :returns: A list of dicts with all attributes of a
            :class:`~genesisng.schema.extra.Extra` model class.
        :rtype: list
        """

        # Database connection
        conn = self.user_config.genesisng.database.connection

        # Cache control default value
        cache_control = self.user_config.genesisng.cache.default_cache_control

        # Check whether a copy exists in the cache
        cache_key = 'all'
        try:
            cache = self.cache.get_cache('builtin', 'extras')
        except Exception:
            self.logger.error("Could not get the 'extras' cache collection.")
        if cache is not None:
            cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.logger.info("Returning list of extras from the cache.")

            self.response.status_code = OK
            # TODO: Check first whether self.environ exists?
            self.environ.status_code = OK
            self.response.headers['Content-Language'] = 'en'
            self.response.payload[:] = cache_data.value
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = str(
                cache_data.last_write_http)
            self.response.headers['ETag'] = str(cache_data.hash)
            return

        # Reuse the session if any has been provided
        if self.environ.session:
            session = self.environ.session
        else:
            session = self.outgoing.sql.get(conn).session()

        # Compose and execute query
        query = session.query(Extra)
        query = query.filter(Extra.deleted.is_(None))
        query = query.order_by(Extra.id.asc())
        result = query.all()

        if not result:
            self.response.status_code = NO_CONTENT
            # TODO: Check first whether self.environ exists?
            self.environ.status_code = NO_CONTENT
            self.response.headers['Cache-Control'] = 'no-cache'

            # Transform the result (a list of objects) into a list of
            # dictionaries so that they can be stored in the cache.
            payload = [r.asdict() for r in result]

            # Store the processed result set in the cache
            if cache is not None:
                cache_data = cache.set(cache_key, payload, details=True)

            self.response.status_code = OK
            # TODO: Check first whether self.environ exists?
            self.environ.status_code = OK
            self.response.payload[:] = payload
            self.response.headers['Content-Language'] = 'en'

            if cache_data:
                self.response.headers['Cache-Control'] = cache_control
                self.response.headers['Last-Modified'] = str(
                    cache_data.last_write_http)
                self.response.headers['ETag'] = str(cache_data.hash)
            else:
                self.response.headers['Cache-Control'] = 'no-cache'

        # Close the session only if we created a new one
        if not self.environ.session:
            session.close()
