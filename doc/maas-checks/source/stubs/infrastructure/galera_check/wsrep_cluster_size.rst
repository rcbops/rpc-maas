Validates returned check metrics from the local ``galera_check.py``
plugin run on the ``galera_all[0]`` inventory node. This alarm evaluates
the output of variable ``wsrep_cluster_size``. The size of the cluster
defaults to the number of nodes in the galera inventory.

If the ``wsrep_cluster_size`` metric is less than the number of
inventory nodes (``{{ groups['galera'] | length }}``) for three
successive intervals, a critical alarm notification is generated. This
indicates that one or more cluster nodes have lost network connectivity
or have failed.
