Utilizes a custom ``agent.plugin`` check type, `nova_service_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nova_service_check.py>`_.
The plugin runs locally from the each ``nova_compute`` inventory node,
if existing in the associated Openstack release version. This check
ensures the ``nova-compute`` service is operationally healthy across all
hosts.

Alarms associated with this monitoring check utilize the
``nova-compute_status`` metric, which is a string:

.. code-block:: console

                     "Yes" : Healthy state
    ".*cannot reach API.*" : Warning state
                      "No" : Error state

An example of properly executing the ``nova_service_check`` plugin:

.. code-block:: console

    root@compute1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      usr/lib/rackspace-monitoring-agent/plugins/nova_service_check.py \
      --host compute1 \
      --protocol http \
      10.0.236.150
    status okay
    metric client_success uint32 1
    metric nova-compute_status string Yes
