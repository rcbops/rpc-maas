Validates returned check metrics from the local ``conntrack_count.py`` plugin
from all nodes. If the percentage of ``nf_conntrack_count`` and
``nf_conntrack_max`` metrics reach the 90% threshold for three successive
intervals, a critical alarm notification is generated. This indicates the
associated node is reaching the a point of which new connections will be
dropped.

The default thresholds are identified below and can be overridden with
different values at run time. While both warning and critical alarm
thresholds exist, it's important to note that only ``critical``
evaluations will result in a ticket being created.
