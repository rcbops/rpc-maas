The Nova category collects metrics and alarms on Nova-related events.
It's driven by the following plugins:

* `nova_api_local_check.py <https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nova_api_local_check.py>`_
* `nova_api_metadata_local_check.py <https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nova_api_metadata_local_check.py>`_
* `nova_service_check.py <https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nova_service_check.py>`_
* `nova_cloud_stats.py <https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/nova_cloud_stats.py>`_

These plugins run contextually on all Nova inventory groups,
``nova_api_metadata``, ``nova_api_os_compute``, ``nova_scheduler``,
``nova_cert``, ``nova_compute``, ``nova_conductor``, and
``nova_console``. Each plugin generates metrics directly against the
Nova API using the OpenStack SDK. This ensures all aspects of the Nova
API are up-and-running. Check templates are deployed to each node in the
aforementioned inventory groups.
