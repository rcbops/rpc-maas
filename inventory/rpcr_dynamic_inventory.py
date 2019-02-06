#!/usr/bin/env python
# need to maake this file executable
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
import getopt
import os
import re
import socket
import sys

from heatclient import client as heat_client
from openstack.connection import Connection
from tripleo_common.inventory import TripleoInventory
from tripleo_validations.utils import get_auth_session

from base_inventory import MaasInventory
from rpcr_tripleo_host_group_mapping import TRIPLEO_MAPPING_GROUP


def validate_ip(s):
    try:
        socket.inet_pton(socket.AF_INET, s)
        return True
    except socket.error:
        return False


class RPCRMaasInventory(MaasInventory):

    def __init__(self):
        # Load stackrc environment variable file
        self.load_rc_file()
        self.load_ca_cert()
        super(RPCRMaasInventory, self).__init__()

    def read_input_inventory(self):
        auth_url = os.environ.get('OS_AUTH_URL')
        os_username = os.environ.get('OS_USERNAME')
        os_project_name = os.environ.get(
            'OS_PROJECT_NAME', os.environ.get('OS_TENANT_NAME'))
        os_password = os.environ.get('OS_PASSWORD')
        os_auth_token = os.environ.get('OS_AUTH_TOKEN')
        os_cacert = os.environ.get('OS_CACERT')
        ansible_ssh_user = os.environ.get('ANSIBLE_SSH_USER', 'heat-admin')
        self.osc_conn = Connection()
        self.undercloud_stack = next(self.osc_conn.orchestration.stacks())
        self.plan_name = (os.environ.get('TRIPLEO_PLAN_NAME') or
                          os.environ.get('STACK_NAME_NAME') or
                          self.get_tripleo_plan_name())
        session = get_auth_session(auth_url,
                                   os_username,
                                   os_project_name,
                                   os_password,
                                   os_auth_token,
                                   os_cacert)
        heat_api_version = (
            self.osc_conn.orchestration.get_api_major_version()[0])
        self.hclient = heat_client.Client(heat_api_version,
                                          session=session)
        inventory = TripleoInventory(
            session=session,
            hclient=self.hclient,
            auth_url=auth_url,
            cacert=os_cacert,
            project_name=os_project_name,
            username=os_username,
            ansible_ssh_user=ansible_ssh_user,
            plan_name=self.plan_name)
        return inventory.list()

    def load_rc_file(self, stack_name='stack'):
        rc_env_file_path = '/home/stack/{stack_name}rc'.format(
            stack_name=stack_name
        )
        if not os.path.exists(rc_env_file_path):
            raise RuntimeError('No {stack_name}rc file found, aborting...'.
                               format(stack_name=stack_name))
        envre = re.compile(
            '^(?:export\s)?(?P<key>\w+)(?:\s+)?=(?:\s+)?(?P<value>.*)$'
        )
        with open(rc_env_file_path) as ins:
            for line in ins:
                match = envre.match(line)
                if match is None:
                    continue
                k = match.group('key')
                v = match.group('value').strip('"').strip("'")
                # (NOTE:tonytan4ever) dealing with case in OSP13:
                # OS_BAREMETAL_API_VERSION=$IRONIC_API_VERSION
                if not v.startswith("$"):
                    os.environ[k] = v

    def load_ca_cert(self):
        # Load the CACERT bundle env variable
        os.environ['OS_CACERT'] = '/etc/pki/tls/certs/ca-bundle.crt'

    def get_tripleo_plan_name(self):
        return self.undercloud_stack.name

    def add_all_group_hosts(self, group_name, input_inventory):
        """Given a group name in input_inventory), recursively add it
        child group and child host
        """
        if 'hosts' in input_inventory[group_name]:
            self.inventory[group_name] = copy.deepcopy(
                input_inventory[group_name]
            )
            # questions: would we have more than one hosts per leaf
            # group ? if so, what is the ansible_host value there?
            # If ansible_host already exists in group vars or host vars
            # do not assign it at host group level
            try:
                if 'ansible_host' not in input_inventory[group_name]['vars']:
                    if validate_ip(input_inventory[group_name]['hosts'][0]):
                        self.inventory[group_name]['vars']['ansible_host'] = (
                            input_inventory[group_name]['hosts'][0])
            except IndexError:
                print("Oops, I didn't find that host.")
                quit()
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
        else:
            self.inventory[group_name] = copy.deepcopy(
                input_inventory[group_name]
            )
            for child in input_inventory[group_name]['children']:
                self.add_all_group_hosts(child, input_inventory)

    def generate_env_specific_variables(self):
        endpointmap_resource = self.hclient.resources.get(self.plan_name,
                                                          'EndpointMap')
        endpointmap_resource_dict = endpointmap_resource.to_dict()[
            'attributes']['endpoint_map']

        self.internal_lb_vip = endpointmap_resource_dict['KeystoneInternal'][
            'host'
        ]
        self.external_lb_vip = endpointmap_resource_dict['KeystonePublic'][
            'host'
        ]

        stack_env_dict = self.osc_conn.orchestration.get_stack_environment(
            self.plan_name
        ).to_dict()['parameter_defaults']

        # get galera root password
        self.galera_password = stack_env_dict['MysqlRootPassword']

        # load overcloud env and osc
        self.load_rc_file(stack_name=self.plan_name)
        tmp_osc_conn = Connection()

        # get cinder_backend_volume fact
        self.cinder_backend_fact = {
        }
        for cinder_backend_pool in tmp_osc_conn.volume.backend_pools():
            backend_host = cinder_backend_pool.name.split('#')[0]
            # (NOTE:tonytan4ever): skip transient legacy backends
            if 'legacy' in backend_host:
                continue
            cinder_backend_pool_dict = cinder_backend_pool.to_dict()[
                'capabilities']
            if 'solidfire' in cinder_backend_pool_dict['volume_backend_name']:
                self.cinder_backend_fact['solidfire'] = {
                    'volume_driver': 'abc',
                    'host': backend_host
                }
            if 'netapp' in cinder_backend_pool_dict['volume_backend_name']:
                self.cinder_backend_fact['netapp'] = {
                    'volume_driver': 'abc',
                    'host': backend_host
                }
            if 'ceph' in cinder_backend_pool_dict['volume_backend_name']:
                self.cinder_backend_fact['ceph'] = {
                    'volume_driver': 'abc',
                    'host': backend_host
                }
        # reset to undercloud rc for osc
        self.load_rc_file()

    def do_host_group_mapping(self, input_inventory):
        for source_group, children_list in TRIPLEO_MAPPING_GROUP.items():
            for child in children_list:
                if (child not in self.inventory and child in input_inventory):
                    self.add_all_group_hosts(child, input_inventory)

            self.inventory[source_group] = {
                'children': children_list
            }

    def generate_inventory(self):
        input_inventory = self.read_input_inventory()
        # generate some product specific variables
        self.generate_env_specific_variables()
        self.inventory['_meta'] = copy.deepcopy(input_inventory['_meta'])
        for host in self.inventory['_meta']['hostvars']:
            (self.inventory['_meta']['hostvars'][host][
                'container_address']) = (
                self.inventory['_meta']['hostvars'][host]['internal_api_ip']
            )
            self.inventory['_meta']['hostvars'][host]['ansible_user'] = (
                'heat-admin')
            (self.inventory['_meta']['hostvars'][host]['ansible_become']) = (
                'yes'
            )
            (self.inventory['_meta']['hostvars'][host]
                ['ansible_ssh_private_key_file']) = (
                    '/home/stack/.ssh/id_rsa'
            )
            (self.inventory['_meta']['hostvars'][host]
                ['galera_root_password']) = (
                    self.galera_password
            )

            (self.inventory['_meta']['hostvars'][host]
                ['internal_lb_vip_address']) = (
                self.internal_lb_vip
            )
            (self.inventory['_meta']['hostvars'][host]
                ['external_lb_vip_address']) = (
                self.external_lb_vip
            )
            (self.inventory['_meta']['hostvars'][host]['maas_stackrc']) = (
                '/home/stack/{plan_name}rc'.format(plan_name=self.plan_name)
            )
            (self.inventory['_meta']['hostvars'][host]
                ['cinder_backends']) = (
                self.cinder_backend_fact
            )
        self.do_host_group_mapping(input_inventory)


def main():
    usage = "USAGE: rpcr_dynamic_inventory.py\n" \
            "--list <list>\n" \
            "--host <host>\n"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "list:host", ["list", "host"])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)


# Get the inventory.
if __name__ == "__main__":
    RPCRMaasInventory()
