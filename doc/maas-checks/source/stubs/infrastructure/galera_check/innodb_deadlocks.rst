Validates returned check metrics from the local ``galera_check.py``
plugin run on the ``galera_all[0]`` inventory node. This alarm uses a
`rate-over-time
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/alert-triggers-and-alarms/#constructs-with-function-modifiers>`_
function to evaluate connections from the output of variable
``Innodb_deadlocks``.

If the ``innodb_deadlocks`` metric is greater than the associated
threshold for three successive intervals, a critical alarm notification
is generated. This indicates that deadlocks are frequently occurring on
the cluster.

The default thresholds are identified below and can be overridden with
different values at run time. While both warning and critical alarm
thresholds exist, it's important to note that only ``critical``
evaluations will result in a ticket being created.
