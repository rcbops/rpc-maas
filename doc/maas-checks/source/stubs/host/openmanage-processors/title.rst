The *openmanage processors* check utilizes a custom plugin,
`openmanage.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/openmanage.py>`_,
which runs locally in all Rackspace data center (RDC) and OpenStack
Everywhere deployments. It leverages the native Dell OpenManage Server Administrator (OMSA)
utilities to provide system-level commands for interfacing with Dell
hardware. This tooling is **not** installed as part of rpc-maas
playbooks, rather it is handled as part of the general deployment and
onboarding of an environment.

.. note::

    Rackspace currently supports the following Dell chassis:

    * Dell PowerEdge R720
    * Dell PowerEdge R740XD
    * Dell PowerEdge R820
    * Dell PowerEdge R840

The plugin executes ``omreport chassis processors`` and returns a
boolean metric with the following values:

.. code-block:: console

    0: Error state
    1: Healthy state

The following snippet is an example of properly executing the
``openmanage`` plugin scoped to processors:

.. code-block:: console

    root@infra01:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/openmanage.py chassis processors
    status okay
    metric hardware_processors_status uint32 1
