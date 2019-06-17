Utilizes a custom ``agent.plugin`` check type, ``ceph_monitoring.py``.
The plugin runs locally from the all Ceph radosgw nodes in the
inventory, resulting in metrics based on the overall health status of
the local radosgw API. Each radosgw address is dynamically generated
based on the HTTP protocol, local address, and port.

Valid ``rgw_up`` metrics are ``0``, ``1``, and ``2`` with the following
descriptions:

.. code-block:: console

    0: RGW node is in ERROR state
    1: RGW node is in WARNING state
    2: RGW node is in OK state

An example of properly executing the ``ceph_rgw_stats`` plugin:

.. code-block:: console

    root@rgw1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/ceph_monitoring.py \
      --name client.raxmon \
      --keyring /etc/ceph/ceph.client.raxmon.keyring \
      rgw \
      --rgw_address http://172.29.236.36:8080
    status okay
    metric rgw_up uint32 2
