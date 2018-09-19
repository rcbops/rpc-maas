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

import copy
import json
import os
try:
    from StringIO import StringIO  # Python2
except ImportError:
    from io import StringIO  # Python3
import sys

from heatclient import client as heat_client
from openstackclient.shell import main
from tripleo_common.inventory import TripleoInventory
from tripleo_validations.utils import get_auth_session

from base_inventory import MaasInventory


def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


class RPCRMaasInventory(MaasInventory):

    def read_input_inventory(self):
        auth_url = os.environ.get('OS_AUTH_URL')
        os_username = os.environ.get('OS_USERNAME')
        os_project_name = os.environ.get(
            'OS_PROJECT_NAME', os.environ.get('OS_TENANT_NAME'))
        os_password = os.environ.get('OS_PASSWORD')
        os_auth_token = os.environ.get('OS_AUTH_TOKEN')
        os_cacert = os.environ.get('OS_CACERT')
        ansible_ssh_user = os.environ.get('ANSIBLE_SSH_USER', 'heat-admin')
        self.plan_name = (os.environ.get('TRIPLEO_PLAN_NAME') or
                          os.environ.get('STACK_NAME_NAME') or "overcloud")
        session = get_auth_session(auth_url,
                                   os_username,
                                   os_project_name,
                                   os_password,
                                   os_auth_token,
                                   os_cacert)
        hclient = heat_client.Client('1', session=session)
        inventory = TripleoInventory(
            session=session,
            hclient=hclient,
            auth_url=auth_url,
            cacert=os_cacert,
            project_name=os_project_name,
            username=os_username,
            ansible_ssh_user=ansible_ssh_user,
            plan_name=self.plan_name)
        return inventory.list()

    def app_all_group_hosts(self, group_name, input_inventory):
        """Given a group name in input_inventory), find out all its
        leaf groups (groups with hosts but no children anymore)

        returns a list of hosts
        """
        if 'hosts' in input_inventory[group_name]:
            self.inventory[group_name] = copy.deepcopy(
                input_inventory[group_name]
            )
            # questions: would we have more than one hosts per leaf
            # group ? if so, what is the ansible_host value there?
            # If ansible_host already exists in group vars or host vars
            # do not assign it at host group level
            if 'ansible_host' in input_inventory[group_name]['vars']:
                pass
            else:
                if validate_ip(input_inventory[group_name]['hosts'][0]):
                    self.inventory[group_name]['vars']['ansible_host'] = (
                            input_inventory[group_name]['hosts'][0])

            # We want undercloud's name hostname to be director
            if group_name.lower() == 'undercloud':
                self.inventory[group_name]['hosts'] = [os.getenv(
                    'MAAS_DIRECTOR_NAME',
                    'director'
                )]
            else:
                if len(self.inventory[group_name]['hosts']) == 1 and \
                        validate_ip(input_inventory[group_name]['hosts'][0]):
                    self.inventory[group_name]['hosts'] = [group_name]
                self.inventory[group_name]['vars']['ansible_user'] = (
                    self.inventory[group_name].get('ansible_ssh_user',
                                                   'heat-admin')
                )
                (self.inventory[group_name]['vars']
                    ['ansible_become']) = (
                        'yes'
                )
                (self.inventory[group_name]['vars']
                    ['ansible_ssh_private_key_file']) = (
                        '/home/stack/.ssh/id_rsa'
                )

                old_stdout = sys.stdout
                endpoint_map_result = StringIO()
                sys.stdout = endpoint_map_result
                main('stack resource show {plan} '
                     'EndpointMap -c attributes -f json'.format(
                         plan=self.plan_name
                     ).split())
                sys.stdout = old_stdout
                endpoint_map_result_json = json.loads(
                    endpoint_map_result.getvalue().strip().rstrip('0'))

                (self.inventory[group_name]['vars']
                    ['internal_lb_vip_address']) = (
                       endpoint_map_result_json['attributes']['endpoint_map']
                       ['KeystoneInternal']['host']
                )
                (self.inventory[group_name]['vars']
                    ['external_lb_vip_address']) = (
                      endpoint_map_result_json['attributes']['endpoint_map']
                      ['KeystonePublic']['host']
                )
        else:
            self.inventory[group_name] = copy.deepcopy(
                input_inventory[group_name]
            )
            for child in input_inventory[group_name]['children']:
                self.app_all_group_hosts(child, input_inventory)

    def generate_mandatory_groups(self, input_inventory):
        mandatory_groups = ["undercloud", "overcloud",
                            "Undercloud", "Overcloud"]
        existing_mandatory_groups = [
            mandatory_group for mandatory_group in mandatory_groups
            if mandatory_group in input_inventory
        ]
        self.inventory["hosts"] = {'children': existing_mandatory_groups}
        self.inventory["all"] = {'children': ['hosts']}
        for key in existing_mandatory_groups:
            self.app_all_group_hosts(key, input_inventory)

    def generate_optional_groups(self, input_inventory):
        pass

    def generate_infrastracture_groups(self, input_inventory):
        self.inventory["shared-infra_hosts"] = {
            'children': ["Controller"]
        }

        utility_groups = ["undercloud", "Undercloud"]
        existing_utility_groups = [
            utility_group for utility_group in utility_groups
            if utility_group in input_inventory
        ]
        self.inventory["utility_all"] = {
            'children': existing_utility_groups
        }

        old_stdout = sys.stdout
        password_result = StringIO()
        sys.stdout = password_result
        main('stack resource show {plan} '
             'MysqlRootPassword -c attributes -f json'.format(
                 plan=self.plan_name
             ).split())
        sys.stdout = old_stdout
        password_result_json = json.loads(password_result.getvalue().
                                          strip().rstrip('0'))
        self.inventory["galera_all"] = {
            'children': ["Controller"],
            'vars': {
                'galera_root_password': (
                   password_result_json['attributes']['value'])
            }
        }

        self.inventory["galera"] = {
             'children': ["Controller"],
             'vars': {}
        }

        self.inventory["rabbitmq_all"] = {
            'children': ["Controller"]
        }

        self.inventory["memcached_all"] = {
            'children': ["Controller"]
        }

        self.inventory["rsyslog_all"] = {
            'children': ["Controller"]
        }

    def generate_openstack_groups(self, input_inventory):
        self.inventory["keystone_all"] = {
            'children': ["Controller"]
        }

        self.generate_nova_groups(input_inventory)
        self.generate_neutron_groups(input_inventory)
        self.generate_glance_groups(input_inventory)
        self.generate_heat_groups(input_inventory)
        self.generate_cinder_groups(input_inventory)
        self.generate_horizon_groups(input_inventory)
        self.generate_swift_groups(input_inventory)

    def generate_nova_groups(self, input_inventory):
        nova_all_groups = [
            'nova_placement', 'nova_conductor', 'nova_metadata',
            'nova_consoleauth', 'nova_api', 'nova_migration_target',
            'nova_compute', 'nova_scheduler', 'nova_libvirt',
            'nova_vnc_proxy'
        ]
        self.inventory["nova_all"] = {
            'children': nova_all_groups
        }
        for nova_group in nova_all_groups:
            self.app_all_group_hosts(nova_group, input_inventory)

        self.inventory["nova_api_metadata"] = {
            'children': ['nova_metadata']
        }

        self.inventory["nova_api_os_compute"] = {
            'children': ['nova_api']
        }

        self.inventory["nova_compute"] = {
            'children': ['Compute']
        }

        self.inventory["nova_console"] = {
            'children': ['nova_consoleauth']
        }

        # skipping nova_conductor and nova_scheduler
        # since they are overlapping with triple O inventory

    def generate_neutron_groups(self, input_inventory):
        neutron_all_groups = [
            'neutron_metadata', 'neutron_dhcp',
            'neutron_plugin_ml2', 'neutron_ovs_agent',
            'neutron_api', 'neutron_l3'
        ]

        self.inventory["neutron_all"] = {
            'children': neutron_all_groups
        }
        for neutron_group in neutron_all_groups:
            self.app_all_group_hosts(neutron_group, input_inventory)

        self.inventory["neutron_server"] = {
            'children': ['neutron_api']
        }

        self.inventory["neutron_dhcp_agent"] = {
            'children': ['neutron_dhcp']
        }

        self.inventory["neutron_l3_agent"] = {
            'children': ['neutron_l3']
        }

        self.inventory["neutron_linuxbridge_agent"] = {
           'children': ['neutron_ovs_agent']
        }

        self.inventory["neutron_openvswitch_agent"] = {
            'children': ['neutron_ovs_agent']
        }

        self.inventory["neutron_metadata_agent"] = {
            'children': ['neutron_metadata']
        }

        # self.inventory["neutron_metering_agent"] = {
        #    'children': ['neutron_metering']
        # }

    def generate_glance_groups(self, input_inventory):
        glance_all_groups = [
            'glance_api', 'glance_registry_disabled'
        ]

        self.inventory["glance_all"] = {
            'children': glance_all_groups
        }

        for glance_group in glance_all_groups:
            self.app_all_group_hosts(glance_group, input_inventory)

    def generate_heat_groups(self, input_inventory):
        heat_all_groups = [
            'heat_api', 'heat_api_cloudwatch_disabled',
            'heat_engine', 'heat_api_cfn'
        ]

        self.inventory["heat_all"] = {
            'children': heat_all_groups
        }

        for heat_group in heat_all_groups:
            self.app_all_group_hosts(heat_group, input_inventory)

        # heat_api and heat_engine have been added,  heat_api_cloudwatch
        # has been deprecated
        # self.inventory["heat_api"] = {
        #    'children': ['heat_api']
        # }

        # self.inventory["heat_engine"] = {
        #    'children': ['heat_engine']
        # }

    def generate_cinder_groups(self, input_inventory):
        cinder_all_groups = [
            'cinder_api', 'cinder_volume',
            'cinder_scheduler'
        ]

        self.inventory["cinder_all"] = {
            'children': cinder_all_groups
        }

        for cinder_group in cinder_all_groups:
            self.app_all_group_hosts(cinder_group, input_inventory)

    def generate_horizon_groups(self, input_inventory):
        horizon_all_groups = [
            'horizon'
        ]

        for horizon_group in horizon_all_groups:
            self.app_all_group_hosts(horizon_group, input_inventory)

    def generate_swift_groups(self, input_inventory):
        swift_all_groups = [
            'swift_ringbuilder', 'swift_storage',
            'swift_proxy',
        ]

        existing_swift_groups = [
            swift_group for swift_group in swift_all_groups
            if swift_group in input_inventory
        ]

        self.inventory["swift_all"] = {
            'children': existing_swift_groups
        }

        for swift_group in existing_swift_groups:
            self.app_all_group_hosts(swift_group, input_inventory)

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}


# Get the inventory.
if __name__ == "__main__":
    RPCRMaasInventory()
