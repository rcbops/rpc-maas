Utilizes a custom ``agent.plugin`` check type, `neutron_service_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/neutron_service_check.py>`_.
The plugin runs locally from the each ``neutron_dhcp_agent`` inventory
node. This check provides granularity at an agent level to ensure the
Neutron DHCP agents are operationally healthy across all backends.

Alarms associated with this monitoring check utilize the
``neutron-dhcp-agent_status`` metric, which is a string:

.. code-block:: console

                     "Yes" : Healthy state
    ".*cannot reach API.*" : Warning state
                      "No" : Error state

An example of properly executing the ``neutron_service_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/neutron_service_check.py \
      --protocol http \
      --host infra1 \
      --fqdn infra1.openstack.local \
      10.0.236.150
    status okay
    metric client_success uint32 1
    metric neutron-metadata-agent_status string Yes
    metric neutron-dhcp-agent_status string Yes
    metric neutron-linuxbridge-agent_status string Yes
    metric neutron-l3-agent_status string Yes
    metric neutron-metering-agent_status string Yes
