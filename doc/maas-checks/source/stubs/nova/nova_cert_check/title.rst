Utilizes a custom ``agent.plugin`` check type, `nova_service_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nova_service_check.py>`_.
The plugin runs locally from the each ``nova_cert`` inventory node, if
existing in the associated Openstack release version. This check ensures
the Nova cert service is operationally healthy across all backends and
services.

Alarms associated with this monitoring check utilize the
``nova-cert_status`` metric, which is a string:

.. code-block:: console

                     "Yes" : Healthy state
    ".*cannot reach API.*" : Warning state
                      "No" : Error state

An example of properly executing the ``nova_service_check`` plugin:

.. code-block:: console

    root@infra01:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/nova_service_check.py \
      --host infra01-nova-cert-container-59be4175 \
      --protocol http \
      10.239.32.10
    status okay
    metric client_success uint32 1
    metric nova-cert_status string Yes
