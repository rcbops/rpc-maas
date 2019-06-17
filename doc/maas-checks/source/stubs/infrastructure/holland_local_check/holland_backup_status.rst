Validates returned check metrics from the local
``holland_local_check.py`` plugin from all galera nodes. If the
``holland_backup_status`` metric is ``0`` for three successive
intervals, a critical alarm notification is generated. This indicates
that the previous holland backup was not created successfully.
