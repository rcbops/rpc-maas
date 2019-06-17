Validates returned check metrics from the local
``bonding_iface_check.py`` plugin from all nodes. If the
``host_bonding_iface_<bondX>_slave_down`` metric is ``1`` for three
successive intervals, a critical alarm notification is generated. This
indicates the associated bond has a sub-interface that is down.
