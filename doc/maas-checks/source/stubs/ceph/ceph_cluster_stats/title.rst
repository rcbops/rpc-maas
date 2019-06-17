Utilizes a custom ``agent.plugin`` check type, ``ceph_monitoring.py``.
The plugin runs locally from the first Ceph mons node of the inventory
and generates metrics based on the overall health status of the cluster.

Valid ``cluster_health`` metrics are ``0``, ``1``, and ``2`` with the
following descriptions:

.. code-block:: console

    0: Cluster is in a HEALTH_ERR state
    1: Cluster is in a HEALTH_WARN state
    2: Cluster is in a HEALTH_OK state


An example of properly executing the ``ceph_cluster_stats`` plugin:

.. code-block:: console

    root@mon1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/ceph_monitoring.py \
      --name client.raxmon \
      --keyring /etc/ceph/ceph.client.raxmon.keyring \
      cluster
    status okay
    metric cluster_health uint32 2
    metric monmap_epoch uint32 1
    metric osdmap_epoch uint32 47
    metric osds_total uint32 6
    metric osds_up uint32 6
    metric osds_in uint32 6
    metric osds_kb_used uint64 669428
    metric osds_kb_avail uint64 18131212
    metric osds_kb uint64 18800640
    metric pgs_active_clean uint32 352
    metric pgs_total uint32 352
