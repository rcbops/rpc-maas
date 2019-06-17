Validates returned check metrics from the local
``cinder_service_check.py`` plugin run across ``cinder_volume`` nodes.
If the ``cinder-volume-<backend_name>_status`` metric is ``0`` for
three successive intervals, a critical alarm notification is generated.
This indicates the Cinder volume API is down on the associated backend
container or host.
