Validates returned check metrics from the local ``galera_check.py``
plugin run on the ``galera_all[0]`` inventory node. This alarm evaluates
the output of variable ``Innodb_row_lock_time_avg``.

If the ``innodb_row_lock_time_avg`` metric is greater than the
associated threshold for three successive intervals, a critical alarm
notification is generated. This indicates that InnoDB tables are
experiencing a heightened duration of being locked.

The default thresholds are identified below and can be overridden with
different values at run time. While both warning and critical alarm
thresholds exist, it's important to note that only ``critical``
evaluations will result in a ticket being created.
