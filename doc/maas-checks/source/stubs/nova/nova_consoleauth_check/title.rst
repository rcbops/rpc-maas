Utilizes a custom ``agent.plugin`` check type, `nova_service_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nova_service_check.py>`_.
The plugin runs locally from the each ``nova_console`` inventory node.
This check ensures the associated ``nova-consoleauth`` service is
operationally healthy across all backends.

Alarms associated with this monitoring check utilize the
``nova-consoleauth_status`` metric, which is a string:

.. code-block:: console

                     "Yes" : Healthy state
    ".*cannot reach API.*" : Warning state
                      "No" : Error state

An example of properly executing the ``service_api_local_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/nova_service_check.py \
      --host infra1-nova-api-container-3232ef40 \
      --protocol http \
      10.0.236.150
    status okay
    metric client_success uint32 1
    metric nova-conductor_status string Yes
    metric nova-consoleauth_status string Yes
    metric nova-scheduler_status string Yes
