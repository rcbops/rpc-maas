Validates returned check metrics from the local ``galera_check.py``
plugin run on the ``galera_all[0]`` inventory node. This alarm evaluates
the output of variables ``Open_files`` and ``open_files_limit``.

If the percentage of ``num_of_open_files`` and ``open_files_limit``
metrics reach the threshold for three successive intervals, a critical
alarm notification is generated. This indicates that the open file limit
is being reached.

The default thresholds are identified below and can be overridden with
different values at run time. While both warning and critical alarm
thresholds exist, it's important to note that only ``critical``
evaluations will result in a ticket being created.
