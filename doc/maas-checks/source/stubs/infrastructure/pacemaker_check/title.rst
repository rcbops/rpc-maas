The *pacemaker* check utilizes a custom plugin, `pacemaker.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/pacemaker.py>`_,
which runs locally on controller nodes to generate a set of metrics
regarding various aspects of overall Pacemaker cluster health. This
check is deployed to all controller nodes using the
``shared-infra_hosts`` inventory group.

The following subset of Pacemaker metrics are used by ticket generating
alarms:

* `Pacemaker cluster node status <infrastructure.html#alarm-pacemaker-nodes-offline-standby>`_ (``pacemaker_status_nodes``)
* `Pacemaker failed actions <infrastructure.html#alarm-pacemaker-failed-actions>`_ (``pacemaker_failed_actions``)
* `Pacemaker failed resources <infrastructure.html#alarm-pacemaker-resource-stop>`_ (``pacemaker_resource_stop``)

The following snippet is an example of properly executing the
``pacemaker`` plugin:

.. code-block:: console

    root@controller1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/pacemaker.py
    status okay
    metric pacemaker_status_nodes string Pacemaker node status is OK
    metric pacemaker_failed_actions string Pacemaker cluster is OK
    metric pacemaker_resource_stop string Pacemaker resources are OK
