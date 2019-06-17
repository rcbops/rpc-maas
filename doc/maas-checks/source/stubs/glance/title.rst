The Glance category is driven by plugins `glance_api_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/glance_api_local_check.py>`_
and `glance_registry_local_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/glance_registry_local_check.py>`_,
which run contextually on ``glance_api`` and ``glance_registry``
inventory groups. These plugins generate metrics via the Glance API at a
local container level and from the load balanced endpoint targeting all
aspects of Glance functionality.

.. note::

    With the release of the Glance v2 API, the Glance registry service
    has been deprecated. In these deployments the check is automatically
    disabled.
