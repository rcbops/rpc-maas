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
import subprocess

from maas_common import metric
from maas_common import print_output

import netiface_check_lib


def bonding_ifaces_check():
    bonding_ifaces = os.listdir("/proc/net/bonding")
    for bonding_iface in bonding_ifaces:
        bonding_iface_check_cmd = ['cat', '/proc/net/bonding/%s'
                                   % bonding_iface]
        bonding_iface_check_cmd_output = subprocess.check_output(
            bonding_iface_check_cmd
        )
        current_active_slave = (
            bonding_iface_check_cmd_output.split('\n')[4].split(':')[1]
        )

        # send out the metric of current active slave interface
        metric('host_bonding_iface_%s_current_active_iface', 'string',
               current_active_slave)


def main(args):
    bonding_ifaces_check()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check statuses of local bonding interfaces')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
