# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from http.client import OK, NO_CONTENT
from zato.server.service import Service
from genesisng.schema.extra import Extra


class List(Service):
    """
    Service class to get the list of available extras for any given room.

    Channel ``/genesisng/extras/list``.

    Uses `SimpleIO`_.

    Stores the list of extras in the ``availability`` cache. Returns
    ``Cache-Control``, ``Last-Modified`` and ``ETag`` headers. Returns a
    ``Content-Language`` header.

    Returns ``OK`` if results have been found, ``NO_CONTENT`` if there are no
    available extras for the room (i.e. the table is empty or all extras have
    been marked as deleted.
    """

    class SimpleIO(object):
        output_optional = ('id', 'code', 'name', 'description', 'price')
        skip_empty_keys = True
        output_repeated = True

    def handle(self):
        """
        Service handler.

        :returns: All available extras, each including all attributes of a
            :class:`~genesisng.schema.extra.Extra` model class.
        :rtype: list
        """

        conn = self.user_config.genesisng.database.connection
        cache_control = self.user_config.genesisng.cache.default_cache_control

        # Check whether a copy exists in the cache
        cache_key = 'all'
        cache = self.cache.get_cache('builtin', 'extras')
        cache_data = cache.get(cache_key, details=True)
        if cache_data:
            self.response.status_code = OK
            self.environ.status_code = OK
            self.response.headers['Cache-Control'] = cache_control
            self.response.headers['Last-Modified'] = cache_data.last_write_http
            self.response.headers['ETag'] = cache_data.hash
            self.response.headers['Content-Language'] = 'en'
            self.response.payload[:] = cache_data.value
            return

        # Reuse the session if any has been provided
        if self.environ.session:
            session = self.environ.session
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
            self.environ.status_code = OK
            self.response.payload[:] = lod
            self.response.headers['Content-Language'] = 'en'
        else:
            self.response.status_code = NO_CONTENT
            self.environ.status_code = NO_CONTENT
            self.response.headers['Cache-Control'] = 'no-cache'
            self.response.headers['Content-Language'] = 'en'

        # Close the session only if we created a new one
        if not self.environ.session:
            session.close()
