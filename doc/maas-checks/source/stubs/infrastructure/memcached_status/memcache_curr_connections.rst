Validates returned check metrics from the local ``memcached_status.py``
plugin from all nodes. If the metric ``memcache_curr_connections``
reaches the threshold for three successive intervals, a critical alarm
notification is generated. This threshold is based on the existing
variable ``memcached_connections`` (default 1024). This indicates the
associated node is reaching the a point of which memcached will no
longer accept additional connections.
