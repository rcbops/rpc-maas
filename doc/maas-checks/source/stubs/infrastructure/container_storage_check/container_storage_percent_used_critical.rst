Validates returned check metrics from the local
``container_storage_check.py`` plugin from all LVM-backed container
nodes. If the ``container_storage_percent_used_critical`` metric is
``0`` for three successive intervals, a critical alarm notification is
generated. This indicates that one or more of the containers on the node
has breached the threshold.
