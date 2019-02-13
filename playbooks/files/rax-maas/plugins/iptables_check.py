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

import subprocess

from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_ok
from maas_common import status


def main():
    iptables_exist = False
    bridge_params = ["bridge-nf-call-arptables", "bridge-nf-call-ip6tables",
                     "bridge-nf-call-iptables"]
    bridge_sysctl = False
    bridge_param_metrics = {}

    # Check if there are instances on this host. If not, we don't care and
    # just pass the check
    try:
        instances = subprocess.check_output(["virsh", "list"]).split('\n')
    except Exception as e:
        status("error", str(e), force_print=False)
    instancesRunning = False
    for instance in instances:
        if "running" in instance:
            instancesRunning = True

    # No instances running, force a successful check run
    if instancesRunning is False:
        iptables_exist = True
        bridge_sysctl = True
        for param in bridge_params:
            bridge_param_metrics[param] = "1"

    # There are instances on this host. Verify appropriate sysctl settings and
    # iptables rules
    else:
        try:
            bridge_sysctl = True
            for param in bridge_params:
                bridge_param_metrics[param] = str(subprocess.check_output(
                    ['cat', '/proc/sys/net/bridge/' + param])).rstrip('\n')
                if bridge_param_metrics[param] != "1":
                    bridge_sysctl = False
        except Exception as e:
            status('error', str(e), force_print=False)

    # Check that iptables rules are in place
    iptables_rules = ''
    try:
        iptables_rules = str(subprocess.check_output(
            ['iptables-save'])).split('\n')
    except Exception as e:
        status('error', str(e), force_print=False)

    iptables_exist = False
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
    with print_output(print_telegraf=False):
        main()
