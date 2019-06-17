The Heat category is driven by plugins `heat_api_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/heat_api_local_check.py>`_,
and `service_api_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/service_api_local_check.py>`_,
which run contextually on ``heat_api``, ``heat_api_cfn``, and
``heat_api_cloudwatch`` inventory groups. These plugins generate metrics
directly against the Heat API using the OpenStack SDK. This ensures all
aspects of the Heat API are up-and-running. Check templates are deployed
to each node in the aforementioned inventory groups.
