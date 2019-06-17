The categorization of Cinder monitoring is driven by plugins
`cinder_api_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/cinder_api_local_check.py>`_,
`cinder_service_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/cinder_service_check.py>`_,
and `vg_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/vg_check.py>`_.
The plugins utilize the Cinder API via the OpenStack SDK to generate
metrics from defined endpoints and their local container backends. Each
plugin is run contextually on each of the following Cinder inventory
groups: ``cinder_api``, ``cinder_scheduler``, ``cinder_backup`` and
``cinder_volume``.
