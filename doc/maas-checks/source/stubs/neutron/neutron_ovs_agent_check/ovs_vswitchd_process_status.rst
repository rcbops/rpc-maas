Validates returned check metrics from the local
``neutron_ovs_agent_check.py`` plugin run across
``neutron_openvswitch_agent`` nodes. If the
``ovs-vswitchd_process_status`` metric is ``0`` for three successive
intervals, a critical alarm notification is generated. This indicates
the Neutron ``ovs-vswitchd`` process is down on the associated backend
container or host.
