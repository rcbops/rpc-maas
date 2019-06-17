Utilizes a custom ``agent.plugin`` check type, `nova_api_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nova_api_local_check.py>`_.
The plugin runs locally from the each ``nova_api_os_compute`` inventory
node. This check subverts the typical load balanced Nova API in order
to validate functionality at the container level. This provides an
additional level of granularity to ensure the Nova API is
operationally healthy across all backends and services.

Alarms associated with this monitoring check utilize the
``nova_api_local_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``nova_api_local_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/nova_api_local_check.py \
      --protocol http \
      --port 8774 \
      10.0.238.136
    status okay
    metric client_success uint32 1
    metric nova_api_local_status uint32 1
    metric nova_api_local_response_time double 89.061 ms
    metric nova_instances_in_state_ACTIVE uint32 1 instances
    metric nova_instances_in_state_SHUTOFF uint32 0 instances
    metric nova_instances_in_state_ERROR uint32 0 instances
    metric nova_instances_in_state_PAUSED uint32 0 instances
    metric nova_instances_in_state_SUSPENDED uint32 0 instances
