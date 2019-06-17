Validates returned check metrics from the local ``ceph_monitoring.py``
plugin. If the ``cluster_health`` metric is ``0`` (indicating
``HEALTH_ERR`` status) for three successive intervals, a critical alarm
notification is generated.
