The *maas_poller_fd_count* check utilizes a custom plugin,
`maas_poller_fd_count.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/maas_poller_fd_count.py>`_,
which runs locally on all controller nodes to generate metrics regarding
the current ``maas_poller_fd_count`` and total ``maas_poller_fd_max``
values. If file descriptors exhaust the maximum limit, the private
``rackspace-monitoring-poller`` will be unable to initiate connections
to poll other nodes.

Alarms associated with this monitoring check are based on a percentage
of ``maas_poller_fd_count`` and ``maas_poller_fd_max`` metrics. These are
evaluated against a threshold that can be overridden.

An example of properly executing the ``maas_poller_fd_count`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/maas_poller_fd_count.py
    status okay
    metric maas_poller_fd_count uint32 9
    metric maas_poller_fd_max uint32 16384
