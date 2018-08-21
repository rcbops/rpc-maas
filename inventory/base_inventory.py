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
import json


class MaasInventory(object):

    def __init__(self):
        self.inventory = {
        }
        self.read_cli_args()

        # main logic, generate inventory dynamically
        self.generate_inventory()

        # Called with `--list`.
        if self.args.list:
            pass
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.host_inventory(self.args.host)
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.empty_inventory()

        print(json.dumps(self.inventory))

    def generate_mandatory_groups(self, input_inventory):
        pass

    def generate_optional_groups(self, input_inventory):
        pass

    def generate_infrastracture_groups(self, input_inventory):
        pass

    def generate_openstack_groups(self, input_inventory):
        pass

    # Example inventory for testing.
    def generate_inventory(self):
        input_inventory = self.read_input_inventory()
        self.generate_mandatory_groups(input_inventory)
        self.generate_optional_groups(input_inventory)
        self.generate_infrastracture_groups(input_inventory)
        self.generate_openstack_groups(input_inventory)

    def host_inventory(self, hostname):
        hostvars = self.inventory[hostname]['vars']
        return {'_meta': {'hostvars': hostvars}}

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', action='store')
        self.args = parser.parse_args()
