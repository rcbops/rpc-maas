The *network_stats* check utilizes a custom plugin,
`network_stats_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/network_stats_check.py>`_,
which runs locally on all physical hosts to generate metrics for errors
on physical interfaces. These metrics are the result of independently
summing the transmit and receive values across all **physical**
interfaces (excluding virtual), within ``/sys/class/net``. These values
are important to monitor as they're easily overlooked during the
troubleshooting process and can lead to intermittent, difficult to
diagnose problems.

Alarm metrics associated with this monitoring check are
``physical_interface_tx_errors`` and ``physical_interface_rx_errors``,
and are evaluated using a `rate-over-time
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/alert-triggers-and-alarms/#constructs-with-function-modifiers>`_
function. This function subtracts the current metric values from the
previous execution's values to determine if there's a consistent stream
of transmit or receive interface errors. The default threshold is ``64``
and is available to be overridden with Ansible.

The following snippet is an example of properly executing the
``network_stats_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/network_stats_check.py
    status okay
    metric physical_interface_rx_errors int64 0
    metric physical_interface_tx_errors int64 0
