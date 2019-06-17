Validates returned check metrics from the local ``cinder_service_check.py``
plugin run across ``cinder_backup`` nodes. If the ``cinder-backup_status``
metric is ``0`` for three successive intervals, a critical alarm
notification is generated. This indicates the Cinder backup service is down on
the associated backend.
