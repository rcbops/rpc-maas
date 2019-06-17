Utilizes a custom ``agent.plugin`` check type, `cinder_service_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/cinder_service_check.py>`_.
The plugin runs locally from the each ``cinder_volume`` inventory node.
This check subverts the typical load balanced Cinder API in order to
validate functionality at the container level. This provides an
additional level of granularity to ensure the Cinder API is
operationally healthy across all backends.

Cinder backend pools are discovered using the Cinder API via the
OpenStack SDK. During the ``maas-sdk-integration.yml`` playbook,
backends are dynamically determined to be part of a shared or local
backend pool. If identical backend services exist for each
``cinder_volume`` node, the associated services are marked as local and
are subsequently monitored on each ``cinder_volume`` node. On the other
hand, if a given backend pool has a single backend service, it's
identified as shared across all ``cinder_volume`` nodes. Subsequently,
this backend will only be enabled and monitored on the first
``cinder_volume`` node as it appears in the inventory, as it would be
duplicative across other nodes.

Alarms associated with this monitoring check utilize the
``cinder-volume-<backend_name>_status`` metric, which is a boolean:

.. code-block:: console

    0: Error state
    1: Healthy state

An example of properly executing the ``cinder_volume_<backend>_check``
plugin for an LVM backed cinder volume:

.. code-block:: console

    root@cinder1:~# /usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh \
      /usr/lib/rackspace-monitoring-agent/plugins/cinder_service_check.py \
      --host cinder1@lvm \
      --protocol http \
      10.0.236.150
    status okay
    metric client_success uint32 1
    metric cinder-volume-lvm_status uint32 1
