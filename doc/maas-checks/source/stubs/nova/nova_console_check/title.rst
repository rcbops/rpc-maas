Utilizes a custom ``agent.plugin`` check type,
`service_api_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/service_api_local_check.py>`_.
The plugin runs locally from the each ``nova_console`` inventory node.
This check ensures the associated nova ``<console_type>`` and it's
associated port are operationally healthy across all backends.

Alarms associated with this monitoring check utilize the
``nova_<console_type>_api_local_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``service_api_local_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/service_api_local_check.py \
      nova_spice \
      10.0.238.136 \
      6082 \
      --path spice_auto.html
    status okay
    metric client_success uint32 1
    metric nova_spice_api_local_status uint32 1
    metric nova_spice_api_local_response_time double 10.140 ms


.. note::

    This example uses a ``spice`` ``<console_type>``. On normal
    deployments, this value is introspected during
    ``maas-pre-flight.yml`` playbook execution and set as a local fact
    within Ansible.
