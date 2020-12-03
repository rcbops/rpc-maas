#!/usr/bin/env python3

# Copyright 2014, Rackspace US, Inc.
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

from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_err_no_exit
from maas_common import status_ok
from maas_common import NEUTRON_AGENT_TYPE_LIST


def check(args):
    neutron = get_openstack_client('network')

    try:
        if args.host:
            agents = [i for i in neutron.agents(host=args.host)]
        elif args.fqdn:
            agents = [i for i in neutron.agents(host=args.fqdn)]
        else:
            agents = [i for i in neutron.agents()]

    # An API status metric is not gathered so catch any exception
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_neutron')
        for neutron_agent_type in NEUTRON_AGENT_TYPE_LIST:
            metric('%s_status' % neutron_agent_type,
                   'string',
                   '%s cannot reach API' % neutron_agent_type,
                   m_name='maas_neutron')
        status_err_no_exit(str(e), m_name='maas_neutron')
        return
    else:
        metric_bool('client_success', True, m_name='maas_neutron')

    if len(agents) == 0:
        status_err("No host(s) found in the agents list",
                   m_name='maas_neutron')

    # Return all the things
    status_ok(m_name='maas_neutron')
    for agent in agents:
        agent_is_up = "Yes"
        if agent['is_admin_state_up'] and not agent['is_alive']:
            agent_is_up = "No"

        if args.host:
            name = '%s_status' % agent['binary']
        elif args.fqdn:
            name = '%s_status' % agent['binary']
        else:
            name = '%s_%s_on_host_%s' % (agent['binary'],
                                         agent['id'],
                                         agent['host'])

        metric(name, 'string', agent_is_up, m_name='maas_neutron')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check neutron agents')
    parser.add_argument('hostname',
                        type=str,
                        help='Neutron API hostname or IP address')
    parser.add_argument('--host',
                        type=str,
                        help='Only return metrics for specified host',
                        default=None)
    parser.add_argument('--fqdn',
                        type=str,
                        help='Only return metrics for specified fqdn',
                        default=None)
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--protocol',
                        type=str,
                        default='http',
                        help='Protocol for client requests')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
