The *conntrack_count* check utilizes a custom plugin, `conntrack_count.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/conntrack_count.py>`_,
which runs locally on all physical hosts to generate metrics regarding the
current ``nf_conntrack_count`` and total ``nf_conntrack_max`` values. If
current conntrack connections exhaust the maximum limit, all subsequent
connections will be dropped on the associated node. This value is
crucial to monitor in OpenStack deployments as differing workloads may
uniquely impact environments.

Alarms associated with this monitoring check are based on a percentage
of ``nf_conntrack_count`` and ``nf_conntrack_max`` metrics. These are
evaluated against a threshold that can be overridden.

An example of properly executing the ``conntrack_count`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/conntrack_count.py
    status okay
    metric nf_conntrack_count uint32 0
    metric nf_conntrack_max uint32 262144
