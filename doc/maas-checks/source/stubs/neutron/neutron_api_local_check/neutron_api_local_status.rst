Validates returned check metrics from the local
``neutron_api_local_check.py`` plugin run across ``neutron_server``
nodes. If the ``neutron_api_local_status`` metric is ``0`` for three
successive intervals, a critical alarm notification is generated. This
indicates the Neutron API is down on the associated backend container or
host.
