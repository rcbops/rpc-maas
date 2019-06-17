The *memcached_status* check utilizes a custom plugin,
`memcached_status.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/memcached_status.py>`_,
which runs locally on controller nodes to generate a set of metrics
regarding various aspects of overall Memcached health. This check is
deployed to all controller nodes using the ``memcached_all`` inventory
group.

The following subset of Memcached metrics are used by ticket generating
alarms:

* `Memcached status <infrastructure.html#alarm-memcache-api-local-status>`_ (``memcache_api_local_status``)
* `Memcached connections <infrastructure.html#alarm-memcache-curr-connections>`_ (``memcache_curr_connections``)

The following snippet is an example of properly executing the
``memcached_status`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/memcached_status.py \
      10.0.238.19
    status okay
    metric client_success uint32 1
    metric memcache_api_local_status uint32 1
    metric memcache_total_items uint64 472035 items
    metric memcache_get_misses uint64 72257 cache_misses
    metric memcache_curr_connections uint64 248 connections
    metric memcache_get_hits uint64 11277458 cache_hits
