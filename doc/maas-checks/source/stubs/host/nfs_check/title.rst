The *nfs_check* utilizes a custom plugin, `nfs_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nfs_check.py>`_,
which runs locally on all physical hosts to generate metrics regarding
NFS. The check currently identifies filesystems with an NFS mount type
in ``/proc/mounts``, and determines whether it's currently running any
exports.

The ``nfs_all_online`` metric associated with this check is a boolean
with the following values:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``nfs_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/nfs_check.py
    status okay
    metric nfs_all_online uint32 1
