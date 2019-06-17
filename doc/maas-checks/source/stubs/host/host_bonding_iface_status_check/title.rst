The *host_bonding_iface_status* check utilizes a custom plugin,
`bonding_iface_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/bonding_iface_check.py>`_,
which runs locally on all physical hosts to generate metrics for each
associated bonding interface. Bonding interfaces are enumerated at
playbook runtime using Ansible facts to determine interfaces with the
``bonding`` interface type.

Alarms associated with this monitoring check are dynamic. Each parent
bonding interface will create an additional alarm criteria and metric,
such as ``host_bonding_iface_<bondX>_slave_down``. The metric is a
boolean with the following values:

.. code-block:: console

    0: Healthy state
    1: Error state

An example of properly executing the ``bonding_iface_check`` plugin:

.. code-block:: console

    root@infra01:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/bonding_iface_check.py
    metric host_bonding_iface_bond0_slave_down uint32 0
    metric host_bonding_iface_bond1_slave_down uint32 0
