Validates returned check metrics from the local
``network_stats_check.py`` plugin from all nodes. If the `rate-over-time
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/alert-triggers-and-alarms/#constructs-with-function-modifiers>`_
of the ``physical_interface_rx_errors`` metric breaches the configured
threshold for three successive intervals, a critical alarm notification
is generated.

The default thresholds are identified below and can be overridden with
different values at run time.
