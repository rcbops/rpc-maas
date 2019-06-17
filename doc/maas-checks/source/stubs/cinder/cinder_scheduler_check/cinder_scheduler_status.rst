Validates returned check metrics from the local
``cinder_service_check.py`` plugin run across ``cinder_scheduler``
nodes. If the ``cinder-scheduler_status`` metric is ``0`` for three
successive intervals, a critical alarm notification is generated. This
indicates the Cinder scheduler service is down on the associated
backend.
