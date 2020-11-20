#!/usr/bin/env python3
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
import copy
import json
import os

from abc import ABCMeta, abstractmethod


class MaasInventory(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.inventory = self.empty_inventory()
        self.read_cli_args()

        # main logic, generate inventory dynamically
        self.generate_inventory()

        # Called with `--list`.
        if self.args.list:
            data = self.inventory
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not needed, since we return `_meta` with `--list`.
            data = self.host_inventory(self.args.host)
        # If no groups or vars are present, return an empty inventory.
        else:
            print("The --host or --list args are required.")
            quit()

        data = json.dumps(data)

        if self.args.outfile:
            self._write_to_file(data, self.args.outfile)
        else:
            print(data)

    def _write_to_file(self, data, path):
        if os.access(os.path.dirname(path), os.W_OK):
            with open(path, 'w') as outfile:
                outfile.write(data)
        else:
            raise RuntimeError("FATAL: Unable to write to {path}".format(
                path=path))

    @abstractmethod
    def generate_env_specific_variables(self):
        return

    @abstractmethod
    def generate_inventory(self):
        return

    def host_inventory(self, hostname):
        try:
            hostvars = copy.deepcopy(self.inventory[hostname]['vars'])
            return {'_meta': {'hostvars': hostvars}}
        except KeyError:
            print("Oops, I didn't find that host.")
            quit()

    # Empty inventory to use as a template
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', action='store')
        parser.add_argument('--outfile', nargs='?',
                            type=str, action='store',
                            default=None)
        self.args = parser.parse_args()
