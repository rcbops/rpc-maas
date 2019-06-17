Validates returned check metrics from the local ``nfs_check.py`` plugin
from all nodes. If the ``nfs_all_online`` metric is ``0`` for three
successive intervals, a critical alarm notification is generated. This
indicates that NFS running in a degraded state.
