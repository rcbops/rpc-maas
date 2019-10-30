#!/usr/bin/env python

# Copyright 2019, Rackspace US, Inc.
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

from maas_common import metric
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def physical_interface_errors():
    vnet_devices = os.listdir('/sys/devices/virtual/net')
    vnet_devices.append('bonding_masters')
    totals = dict()
    totals['rx_errors'] = 0
    totals['tx_errors'] = 0
    for d in os.listdir('/sys/class/net'):
        if d not in vnet_devices:
            for e in 'rx_errors', 'tx_errors':
                filepath = '/sys/class/net/%s/statistics/%s' % (d, e)
                with open(filepath, 'r') as f:
                    totals[e] += int(f.read())
                    f.close()
    return totals


def get_softnet_stats():
    softnet_stats = dict()
    softnet_stats['packet_drop'] = 0
    softnet_stats['time_squeeze'] = 0
    with open('/proc/net/softnet_stat', 'r') as f:
        for line in f:
            softnet_stats['packet_drop'] += int(line.split()[1], 16)
            softnet_stats['time_squeeze'] += int(line.split()[2], 16)
    return softnet_stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Network error statistics '
                                     'check')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        try:
            totals = physical_interface_errors()
            softnet_stats = get_softnet_stats()
        except Exception as e:
            status_err(e, m_name='maas_network_stats')
        else:
            status_ok(m_name='maas_network_stats')
            for k, v in totals.items():
                metric('physical_interface_%s' % k, 'int64', v)
            for k, v in softnet_stats.items():
                metric('softnet_stats_%s' % k, 'int64', v)
