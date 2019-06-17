Utilizes a custom ``agent.plugin`` check type, ``ceph_monitoring.py``.
The plugin runs locally from the first Ceph mons node of the inventory
and generates metrics based on the mons quorum status within the cluster.

The ``mon_in_quorum`` metric is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``ceph_mons_stats`` plugin:

.. code-block:: console

    root@mon1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/ceph_monitoring.py \
      --name client.raxmon \
      --keyring /etc/ceph/ceph.client.raxmon.keyring \
      mon \
      --host mon1
    status okay
    metric mon_in_quorum uint32 1
