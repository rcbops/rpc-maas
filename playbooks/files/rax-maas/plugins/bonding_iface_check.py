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

from maas_common import metric_bool
from maas_common import print_output

import netiface_check_lib


def bonding_ifaces_check():
    bonding_ifaces = os.lisdir("/proc/net/bonding")
    for bonding_iface in bonding_ifaces:
        if not netiface_check_lib.is_interface_up(bonding_iface):
            metric_bool('host_bonding_iface_%s_status' % bonding_iface,
                        False,
                        m_name='maas_host_bonding_iface')
        else:
            metric_bool('host_bonding_iface_%s_status' % bonding_iface,
                        True,
                        m_name='maas_host_bonding_iface')


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
