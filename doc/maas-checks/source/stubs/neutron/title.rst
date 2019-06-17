The Neutron category collects metrics and alarms on Neutron-related
events. It's driven by the following plugins:

* `neutron_api_local_check.py <https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/neutron_api_local_check.py>`_
* `neutron_service_check.py <https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/neutron_service_check.py>`_
* `neutron_ovs_agent_check.py <https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/neutron_ovs_agent_check.py>`_

These plugins run contextually on all neutron inventory groups,
``neutron_server``, ``neutron_dhcp_agent``, ``neutron_l3_agent``,
``neutron_linuxbridge_agent``, ``neutron_openvswitch_agent``,
``neutron_metadata_agent``, and ``neutron_metering_agent``. Each plugin
generates metrics directly against the Neutron API using the OpenStack
SDK. This ensures all aspects of the Neutron API are up-and-running.
Check templates are deployed to each node in the aforementioned
inventory groups.
