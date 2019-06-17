Validates check metrics from the native ``agent.memory`` functionality
for all ``infra_hosts`` inventory hosts. If the percentage of
``actual_used`` and ``total`` falls below the ``1`` percent threshold for 3
successive intervals, a critical alarm notification is generated. This
is typically indicative of an issue as the infrastructure hosts should
not be resource constrained.

The default thresholds are identified below and can be overridden with
different values at run time. While both warning and critical alarm
thresholds exist, it's important to note that only ``critical``
evaluations will result in a ticket being created.
