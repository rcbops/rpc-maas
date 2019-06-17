The *hp_monitoring* check utilizes a custom plugin, `hp_monitoring.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/hp_monitoring.py>`_,
which runs locally in all Rackspace data center (RDC) and OpenStack
Everywhere deployments. It leverages the native HP Management Control
Pack (MCP) utilities to provide system-level commands for interfacing
with HP hardware. This tooling is **not** installed as part of rpc-maas
playbooks, rather it is handled as part of the general deployment and
onboarding of an environment.

.. note::

    Rackspace currently supports the HP ``DL 380 Gen 9`` and ``DL 380
    Gen 10`` chassis:

The plugin generates boolean metrics based on the status of the following
hardware components:

* Processor (``hardware_processors_status``)
* Memory (``hardware_memory_status``)
* Power supply (``hardware_powersupply_status``)
* Disk (``hardware_disk_status``)
* RAID controller (``hardware_controller_status``)
* RAID battery (``hardware_controller_battery_status``)
* RAID cache (``hardware_controller_cache_status``)

An example of properly executing the ``hp_monitoring`` plugin:

.. code-block:: console

    root@infra01:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/hp_monitoring.py
    status okay
    metric hardware_memory_status uint32 1
    metric hardware_controller_status uint32 1
    metric hardware_powersupply_status uint32 1
    metric hardware_controller_battery_status uint32 1
    metric hardware_processors_status uint32 1
    metric hardware_controller_cache_status uint32 1
    metric hardware_disk_status uint32 1
