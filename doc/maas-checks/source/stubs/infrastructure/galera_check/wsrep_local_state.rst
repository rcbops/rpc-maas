Validates returned check metrics from the local ``galera_check.py``
plugin run on the ``galera_all[0]`` inventory node. This alarm evaluates
the output of variable ``wsrep_local_state_comment``.

If the ``wsrep_local_state_comment`` metric is any value other than
``Synced`` for three successive intervals, a critical alarm notification
is generated. This indicates that the cluster node is not in-sync.
