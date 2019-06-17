Validates returned check metrics from the local ``memcached_status.py``
plugin run across ``memcached_all`` nodes. If the
``memcache_api_local_status`` metric is ``0`` for three successive
intervals, a critical alarm notification is generated. This indicates
the Memcached API is down on the associated backend.
