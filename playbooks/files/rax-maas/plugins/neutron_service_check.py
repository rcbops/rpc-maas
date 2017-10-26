#!/usr/bin/env python

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

from maas_common import get_neutron_client
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def check(args):

    NETWORK_ENDPOINT = '{protocol}://{hostname}:9696'.format(
        protocol=args.protocol, hostname=args.hostname)
    try:
        neutron = get_neutron_client(endpoint_url=NETWORK_ENDPOINT)

    # not gathering api status metric here so catch any exception
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_neutron')
        status_err(str(e), m_name='maas_neutron')
    else:
        metric_bool('client_success', True, m_name='maas_neutron')

    # gather neutron service states
    if args.host:
        agents = neutron.list_agents(host=args.host)['agents']
    elif args.fqdn:
        agents = neutron.list_agents(host=args.fqdn)['agents']
    else:
        agents = neutron.list_agents()['agents']

    if len(agents) == 0:
        metric_bool('agents_found', False, m_name='maas_neutron')
        status_err("No host(s) found in the agents list",
                   m_name='maas_neutron')
    else:
        metric_bool('agents_found', True, m_name='maas_neutron')

    # return all the things
    status_ok(m_name='maas_neutron')
    for agent in agents:
        agent_is_up = True
        if agent['admin_state_up'] and not agent['alive']:
            agent_is_up = False

        if args.host:
            name = '%s_status' % agent['binary']
        elif args.fqdn:
            name = '%z_status' % agent['binary']
        else:
            name = '%s_%s_on_host_%s' % (agent['binary'],
                                         agent['id'],
                                         agent['host'])

        metric_bool(name, agent_is_up, m_name='maas_neutron')


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
