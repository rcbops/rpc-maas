#!/usr/bin/env python3

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
import subprocess

from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_ok
from maas_common import status


def main():
    nova = get_openstack_client('compute')

    iptables_exist = False
    bridge_sysctl = False
    bridge_params = ["bridge-nf-call-arptables",
                     "bridge-nf-call-ip6tables",
                     "bridge-nf-call-iptables"]
    bridge_param_metrics = {}

    # Check for active instances on the host. If none are found, simply
    # force the check to pass.
    #
    # A power_state of 1 means the instance is 'running'
    try:
        instances = [i for i in nova.servers(host=args.host)
                     if i.power_state == 1 and
                     i.vm_state == 'active']
    except Exception as e:
        status("error", str(e), force_print=False)

    else:
        if len(instances) > 0:
            instances_running = True
        else:
            instances_running = False

        # No instances are active so force the metrics to pass
        if instances_running is False:
            iptables_exist = True
            bridge_sysctl = True
            for param in bridge_params:
                bridge_param_metrics[param] = "1"
        else:
            try:
                bridge_sysctl = True
                for param in bridge_params:
                    bridge_param_metrics[param] = \
                        subprocess.check_output(['cat',
                                                '/proc/sys/net/bridge/' +
                                                 param]
                                                ).decode().rstrip('\n')
                    if bridge_param_metrics[param] != "1":
                        bridge_sysctl = False
            except Exception as e:
                status('error', str(e), force_print=False)

            # Check if iptables rules are in place
            iptables_rules = ''
            try:
                iptables_rules = subprocess.check_output(
                    ['iptables-save']).decode().split('\n')
            except Exception as e:
                status('error', str(e), force_print=False)

            for rule in iptables_rules:
                if "DROP" in rule:
                    iptables_exist = True

    if bridge_sysctl is True and iptables_exist is True:
        metric_bool('iptables_status', True, m_name='iptables_active')
        status_ok(m_name='iptables_active')
    else:
        metric_bool('iptables_status', False, m_name='iptables_active')

    metric('bridge-nf-call-arptables', 'int64',
           bridge_param_metrics.get('bridge-nf-call-arptables', 0))
    metric('bridge-nf-call-iptables', 'int64',
           bridge_param_metrics.get('bridge-nf-call-iptables', 0))
    metric('bridge-nf-call-ip6tables', 'int64',
           bridge_param_metrics.get('bridge-nf-call-ip6tables', 0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Ensure that security groups are being actively '
                    'enforced on a hypervisor.')
    parser.add_argument('host', nargs='?',
                        type=str,
                        help='Compute host to filter')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main()
