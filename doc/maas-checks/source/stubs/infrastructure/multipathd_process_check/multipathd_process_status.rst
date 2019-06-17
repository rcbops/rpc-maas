Validates returned check metrics from the local
``process_check_host.py`` plugin from all nodes. If the
``multipathd_process_status`` metric is ``0`` for three successive
intervals, a critical alarm notification is generated. This indicates
that multipathd service is not currently running.
