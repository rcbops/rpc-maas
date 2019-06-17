Validates returned check metrics from the local ``ceph_monitoring.py``
plugin. If the ``cluster_health`` metric is ``1`` (indicating
``HEALTH_WARN`` status) for three successive intervals, a critical alarm
notification is generated.
