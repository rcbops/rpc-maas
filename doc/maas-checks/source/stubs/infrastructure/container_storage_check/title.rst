The *container_storage* check utilizes a custom plugin,
`container_storage_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/container_storage_check.py>`_,
which runs locally on all LVM-backed LXC container nodes to generate a
boolean metric for whether container filesystems are at risk of filling.
The check will chroot itself into the container (``/proc/<pid>/root``)
and calculate a used percentage.

Alarm metrics associated with this monitoring check are
``container_storage_percent_used_critical``. The default threshold is
set at ``85%`` and is available to be overridden with Ansible at
playbook runtime. The metric descriptions are as follows:

.. code-block:: console

    0: Error state
    1: Healthy state

The following snippet is an example of properly executing the
``container_storage_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/container_storage_check.py \
      --thresh 85
    status okay
    metric container_storage_percent_used_critical uint32 1
