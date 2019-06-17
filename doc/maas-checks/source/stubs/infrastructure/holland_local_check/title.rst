The *holland_local_check* utilizes a custom plugin,
`holland_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/holland_local_check.py>`_,
which runs locally on all ``galera_all`` nodes to generate a boolean
metric for whether a recent holland backup was successfully created. The
check will utilize the defined ``rpc_support_holland_password`` and
`holland playbook
<https://github.com/rcbops/openstack-ops/blob/master/playbooks/install-holland-db-backup.yml>`_
deployed as part of the RPC `openstack-ops
<https://github.com/rcbops/openstack-ops>`_ repository (RPC-O only). The
virtual environment deployment location and version are introspected
from the galera container at playbook runtime.

The alarm metric associated with this monitoring check is
``holland_backup_status``. It is a boolean metric identified by the
following values:

.. code-block:: console

    0: No recent backup found
    1: Recent backup found

The following snippet is an example of properly executing the
``holland_local_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/holland_local_check.py \
      infra1_galera_container-dfa7e5f3 \
      /openstack/venvs/holland-19.0.0.0rc5.dev1/bin/holland
    status okay
    metric holland_backup_status uint32 1
    metric holland_backup_size double 4.73828125 Megabytes
