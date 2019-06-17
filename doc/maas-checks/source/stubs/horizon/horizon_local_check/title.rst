Utilizes a custom ``agent.plugin`` check type, `horizon_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/horizon_check.py>`_.
The check plugin runs locally from the ``horizon[0]`` inventory node
against the load balanced Horizon VIP in order to validate functionality
of the dashboard.

Alarms associated with this monitoring check utilize the
``horizon_local_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``horizon_local_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/horizon_check.py \
      10.0.236.150 \
      openstack \
      --protocol https \
      --port 443
    status okay
    metric client_success uint32 1
    metric horizon_local_status uint32 1
    metric splash_status_code uint32 200 http_code
    metric splash_milliseconds double 48.527 ms
    metric login_status_code uint32 200 http_code
    metric login_milliseconds double 675.014 ms
