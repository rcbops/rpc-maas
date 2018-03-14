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
import time

import ipaddr
from maas_common import get_neutron_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from neutronclient.client import exceptions as exc


def check(args):

    network_endpoint = '{protocol}://{ip}:{port}'.format(
        ip=args.ip,
        protocol=args.protocol,
        port=args.port
    )

    is_up = False
    try:
        if args.ip:
            neutron = get_neutron_client(endpoint_url=network_endpoint)
        else:
            neutron = get_neutron_client()

        is_up = True
    # if we get a NeutronClientException don't bother sending any other metric
    # The API IS DOWN
    except exc.NeutronClientException:
        metric_bool('client_success', False, m_name='maas_neutron')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_neutron')
        status_err(str(e), m_name='maas_neutron')
    else:
        metric_bool('client_success', True, m_name='maas_neutron')
        # time something arbitrary
        start = time.time()
        neutron.list_agents()
        end = time.time()
        milliseconds = (end - start) * 1000

        # gather some metrics
        networks = len(neutron.list_networks()['networks'])
        agents = len(neutron.list_agents()['agents'])
        routers = len(neutron.list_routers()['routers'])
        subnets = len(neutron.list_subnets()['subnets'])

    status_ok(m_name='maas_neutron')
    metric_bool('neutron_api_local_status', is_up, m_name='maas_neutron')
    # only want to send other metrics if api is up
    if is_up:
        metric('neutron_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')
        metric('neutron_networks', 'uint32', networks, 'networks')
        metric('neutron_agents', 'uint32', agents, 'agents')
        metric('neutron_routers', 'uint32', routers, 'agents')
        metric('neutron_subnets', 'uint32', subnets, 'subnets')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Neutron API against local or remote address')
    parser.add_argument('ip', nargs='?',
                        type=ipaddr.IPv4Address,
                        help='Optional Neutron API server address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        action='store',
                        default='9696',
                        help='Port for neutron API service')
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help='Protocol for the neutron API service')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
