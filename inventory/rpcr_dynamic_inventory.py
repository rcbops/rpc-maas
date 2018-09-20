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

import argparse
import os

from heatclient import client as heat_client
from tripleo_common.inventory import TripleoInventory
from tripleo_validations.utils import get_auth_session

from base_inventory import MaasInventory


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
        plan_name = (os.environ.get('TRIPLEO_PLAN_NAME') or
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
            plan_name=plan_name)
        return inventory.list()

    def app_all_group_hosts(self, group_name, input_inventory):
        """Given a group name in input_inventory), find out all its
        leaf groups (groups with hosts but no children anymore)

        returns a list of hosts
        """
        if 'hosts' in input_inventory[group_name]:
            self.inventory[group_name] = input_inventory[group_name]
            # questions: would we have more than one hosts per leaf
            # group ? if so, what is the ansible_host value there?
            self.inventory[group_name]['vars']['ansible_host'] = (
                    self.inventory[group_name]['hosts'][0])
        else:
            self.inventory[group_name] = input_inventory[group_name]
            for child in input_inventory[group_name]['children']:
                self.app_all_group_hosts(child, input_inventory)

    def generate_mandatory_groups(self, input_inventory):
        self.inventory["hosts"] = {'children': ["undercloud", "overcloud"]}
        self.inventory["all"] = {'children': ['hosts']}
        for key in ["undercloud", "overcloud"]:
            self.app_all_group_hosts(key, input_inventory)

    def generate_optional_groups(self, input_inventory):
        pass

    def generate_infrastracture_groups(self, input_inventory):
        pass

    def generate_openstack_groups(self, input_inventory):
        pass

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', action='store')
        self.args = parser.parse_args()


# Get the inventory.
if __name__ == "__main__":
    RPCRMaasInventory()
