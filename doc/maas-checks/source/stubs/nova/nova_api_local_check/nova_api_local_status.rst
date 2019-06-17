Validates returned check metrics from the local
``nova_api_local_check.py`` plugin run across ``nova_api_os_compute``
nodes. If the ``nova_api_local_status`` metric is ``0`` for three
successive intervals, a critical alarm notification is generated. This
indicates the Nova API is down on the associated backend container or
host.
