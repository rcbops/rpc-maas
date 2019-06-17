Utilizes a custom ``agent.plugin`` check type,
`cinder_api_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/cinder_api_local_check.py>`_.
The plugin runs locally from the each ``cinder_api`` inventory node.
This check subverts the typical load balanced Cinder API in order to
validate functionality at the container level. This provides an
additional level of granularity to ensure the Cinder API is
operationally healthy across all backends.

Alarms associated with this monitoring check utilize the
``cinder_api_local_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``cinder_api_local_check`` plugin:

.. code-block:: console

    root@infra1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/cinder_api_local_check.py \
      --protocol http \
      --port 8776 \
      10.0.239.229
    status okay
    metric client_success uint32 1
    metric cinder_api_local_status uint32 1
    metric cinder_api_local_response_time double 51.978 ms
    metric total_cinder_volumes uint32 0 volumes
    metric cinder_available_volumes uint32 0 volumes
    metric cinder_in-use_volumes uint32 0 volumes
    metric cinder_error_volumes uint32 0 volumes
    metric total_cinder_snapshots uint32 0 snapshots
    metric cinder_available_snaps uint32 0 snapshots
    metric cinder_in-use_snaps uint32 0 snapshots
    metric cinder_error_snaps uint32 0 snapshots
