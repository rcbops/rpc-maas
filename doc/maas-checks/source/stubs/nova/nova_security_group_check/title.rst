Utilizes a custom ``agent.plugin`` check type, `iptables_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/iptables_check.py>`_.
The plugin runs locally from the each ``nova_compute`` inventory node.
This check ensures that security groups are properly enforcing on all
compute nodes with active instances.

Alarms associated with this monitoring check utilize the
``iptables_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``iptables_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/iptables_check.py
    status okay
    metric iptables_status uint32 1
    metric bridge-nf-call-arptables int64 1
    metric bridge-nf-call-iptables int64 1
    metric bridge-nf-call-ip6tables int64 1
