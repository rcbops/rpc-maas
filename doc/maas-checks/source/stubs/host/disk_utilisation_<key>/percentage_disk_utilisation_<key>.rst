Validates returned check metrics from the local ``disk_utilisation.py``
plugin. If the ``disk_utilisation_<key>`` metric reaches a 99% threshold
for three successive intervals, a critical alarm notification is
generated.

The default thresholds are identified below and can be overridden with
different values at run time. While both warning and critical alarm
thresholds exist, it's important to note that only ``critical``
evaluations will result in a ticket being created.
