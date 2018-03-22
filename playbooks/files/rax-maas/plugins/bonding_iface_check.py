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

from maas_common import metric_bool
from maas_common import print_output


def bonding_ifaces_check(_):
    bonding_ifaces = os.listdir("/proc/net/bonding")
    for bonding_iface in bonding_ifaces:
        bonding_iface_check_cmd = ['cat', '/proc/net/bonding/%s'
                                   % bonding_iface]
        bonding_iface_check_cmd_output = subprocess.check_output(
            bonding_iface_check_cmd
        )

        bonding_iface_check_cmd_output_lines = (
            bonding_iface_check_cmd_output.split('\n')[1]
        )

        for idx, line in enumerate(bonding_iface_check_cmd_output_lines):
            if line.startswith("Slave Interface"):
                slave_inface_mii_status_line = (
                    bonding_iface_check_cmd_output_lines[idx + 1]
                )
                slave_inface_mii_status = (
                    slave_inface_mii_status_line.split(":")
                )
                if 'down' in slave_inface_mii_status:
                    metric_bool('host_bonding_iface_%s_slave_down' %
                                bonding_iface,
                                True)
                else:
                    metric_bool('host_bonding_iface_%s_slave_down' %
                                bonding_iface,
                                False)


def main(args):
    bonding_ifaces_check(args)


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
