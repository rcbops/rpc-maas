The *multipathd_process_check* utilizes a custom plugin,
`process_check_host.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/process_check_host.py>`_,
which runs locally on all ``cinder_volume`` and ``nova_compute``
inventory nodes and generates metrics regarding the ``multipathd``
process name. This check is contextually deployed when the
``multipathd`` service is running and ``multipath -l`` returns output
indicating connections.

The ``multipathd_process_status`` metric associated with this check is a
boolean with the following values:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``process_check_host``
plugin:

.. code-block:: console

    root@cinder1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/process_check_host.py \
      multipathd
    status okay
    metric multipathd_process_status uint32 1
