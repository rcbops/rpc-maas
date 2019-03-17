#!/usr/bin/env python
# Copyright 2018, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

TRIPLEO_MAPPING_GROUP = {
    # maas mandatory groups
    'hosts': ['undercloud', 'overcloud', 'Undercloud', 'Overcloud'],
    'all': ['hosts'],


    # maas optional groups
    'ceph_all': ['ceph_osd', 'ceph_mon', 'ceph_rgw'],
    'mons': ['ceph_mon'],
    'osds': ['ceph_osd'],
    'rgws': ['ceph_rgw'],


    # maas infrastructure groups
    'shared-infra_hosts': ['Controller', 'controller'],
    'rabbitmq_all': ['Controller', 'controller'],
    'memcached_all': ['Controller', 'controller'],
    'galera_all': ['Controller', 'controller'],
    'galera': ['Controller', 'controller'],
    'rsyslog_all': ['Controller', 'controller'],
    'utility_all': ['undercloud', 'Undercloud'],
    'localhost': ['undercloud', 'Undercloud'],


    # maas openstack groups
    # keystone
    'keystone_all': ['Controller', 'controller'],

    # nova
    'nova_all': [
        'nova_placement', 'nova_conductor', 'nova_metadata',
        'nova_consoleauth', 'nova_api', 'nova_migration_target',
        'nova_compute', 'nova_scheduler', 'nova_libvirt',
        'nova_vnc_proxy'
    ],
    'nova_api_metadata': ['nova_metadata'],
    'nova_api_os_compute': ['nova_api'],
    'nova_compute': ['Compute'],
    'nova_console': ['nova_consoleauth'],

    # neutron
    'neutron_all': [
        'neutron_metadata', 'neutron_dhcp',
        'neutron_plugin_ml2', 'neutron_ovs_agent',
        'neutron_api', 'neutron_l3'
    ],
    'neutron_server': ['neutron_api'],
    'neutron_dhcp_agent': ['neutron_dhcp'],
    'neutron_l3_agent': ['neutron_l3'],
    'neutron_linuxbridge_agent': ['neutron_ovs_agent'],
    'neutron_openvswitch_agent': ['neutron_ovs_agent'],
    'neutron_metadata_agent': ['neutron_metadata'],

    # glance
    'glance_all': ['glance_api', 'glance_registry_disabled'],

    # heat
    'heat_all': ['heat_api', 'heat_api_cloudwatch_disabled',
                 'heat_engine', 'heat_api_cfn'],

    # cinder
    'cinder_all': ['cinder_api', 'cinder_volume', 'cinder_scheduler'],

    # horizon
    'horizon_all': ['horizon'],

    # NOTE(npawelek): These mappings are not confirmed yet. We're not
    # currently deploying ironic to customers due to RFEs around multi
    # tenancy. When this functionality is needed, we'll need to define
    # all the groupings properly.
    #
    # ironic
    # 'ironic_all': ['ironic_api', 'ironic_compute', 'ironic_conductor'],
    # 'ironic_api': ['ironic_api'],
    # 'ironic_conductor': ['ironic_conductor'],
    # 'ironic_compute': ['ironic_compute'],

    # NOTE(npawelek): These mappings are not confirmed yet.
    # 'designate_all': ['designate_all'],
    # 'octavia_all': [
    #     'octavia_api', 'octavia_health_manager', 'octavia_housekeeping',
    #     'octavia_worker'
    # ],
    # 'octavia_api': ['octavia_api'],

    # skip swift_proxy because swift_proxy already exists in tripleo
    'swift_all': ['swift_proxy', 'swift_storage'],
    'swift_hosts': ['swift_storage'],
    'swift_acc': ['swift_storage'],
    'swift_cont': ['swift_storage'],
    'swift_obj': ['swift_storage'],
}
