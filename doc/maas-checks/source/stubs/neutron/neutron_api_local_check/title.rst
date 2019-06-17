Utilizes a custom ``agent.plugin`` check type,
`neutron_api_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/neutron_api_local_check.py>`_.
The plugin runs locally from the each ``neutron_server`` inventory node.
This check subverts the typical load balanced Neutron API in order to
validate functionality at the container level. This provides an
additional level of granularity to ensure the Neutron API is
operationally healthy across all backends and services.

Alarms associated with this monitoring check utilize the
``neutron_api_local_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``neutron_api_local_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/neutron_api_local_check.py \
      --port 9696 \
      --protocol http \
      10.0.238.173
    status okay
    metric client_success uint32 1
    metric neutron_api_local_status uint32 1
    metric neutron_api_local_response_time double 19.989 ms
    metric neutron_agents uint32 17 agents
    metric neutron_networks uint32 2 networks
    metric neutron_routers uint32 1 agents
    metric neutron_subnets uint32 2 subnets
