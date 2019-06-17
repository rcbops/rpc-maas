Utilizes a custom ``agent.plugin`` check type,
`neutron_ovs_agent_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/neutron_ovs_agent_check.py>`_.
The plugin runs locally from the each ``neutron_openvswitch_agent``
inventory node. This check provides granularity at an agent level to
ensure the Neutron openvswitch agents and processes are operationally
healthy across all backends.

Alarms associated with this monitoring check utilize the
``neutron-openvswitch-agent_status`` metric, which is a string:

.. code-block:: console

                     "Yes" : Healthy state
    ".*cannot reach API.*" : Warning state
                      "No" : Error state

Additionally, the ``ovsdb-server_process_status`` and
``ovs-vswitchd_process_status`` metrics are booleans with the following
values:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``neutron_ovs_agent_check`` plugin:

.. code-block:: console

    root@controller0:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/neutron_ovs_agent_check.py \
      --protocol http \
      --host overcloud-controller-0.localdomain \
      --fqdn overcloud-controller-0.localdomain \
      192.168.24.12
    status okay
    metric client_success uint32 1
    metric neutron-openvswitch-agent_status string Yes
    metric ovsdb-server_process_status uint32 1
    metric ovs-vswitchd_process_status uint32 1
