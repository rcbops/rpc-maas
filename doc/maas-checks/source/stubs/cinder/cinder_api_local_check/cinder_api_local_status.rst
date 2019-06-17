Validates returned check metrics from the local
``cinder_api_local_check.py`` plugin run across ``cinder_api`` nodes. If
the ``cinder_api_local_status`` metric is ``0`` for three successive
intervals, a critical alarm notification is generated. This indicates
the Cinder API is down on the associated backend container or host.
