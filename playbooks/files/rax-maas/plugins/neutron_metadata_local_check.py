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
import shlex
import subprocess

from maas_common import get_neutron_client
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok

# identify the first active neutron agents container on this host
# network namespaces can only be accessed from within neutron agents container
FIND_CONTAINER = shlex.split('lxc-ls -1 --running .*neutron_agents')
SERVICE_CHECK = 'ip netns exec %s curl -fvs 169.254.169.254:80'


def check(args):
    # identify the container we will use for monitoring
    try:
        containers_list = subprocess.check_output(FIND_CONTAINER)
        container = containers_list.splitlines()[0]
    except (IndexError, subprocess.CalledProcessError):
        metric_bool('agents_found', False, m_name='maas_neutron')
        status_err('no running neutron agents containers found',
                   m_name='maas_neutron')
    else:
        metric_bool('agents_found', True, m_name='maas_neutron')

    network_endpoint = '{protocol}://{host}:{port}'.format(
        host=args.neutron_host,
        protocol=args.protocol,
        port=args.port
    )
    try:
        neutron = get_neutron_client(endpoint_url=network_endpoint)

    # not gathering api status metric here so catch any exception
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_neutron')
        status_err(str(e), m_name='maas_neutron')
    else:
        metric_bool('client_success', True, m_name='maas_neutron')

    # only check networks which have a port with DHCP enabled
    ports = neutron.list_ports(device_owner='network:dhcp')['ports']
    nets = set([p['network_id'] for p in ports])

    # perform checks for each identified network
    failures = []
    for net_id in nets:
        namespace = 'qdhcp-%s' % net_id
        service_check_cmd = SERVICE_CHECK % namespace
        command = shlex.split('lxc-attach -n %s -- %s' % (container,
                                                          service_check_cmd))
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            # HTTP 404 response indicates the service is responsive.
            # this is the expected response because the maas testing host IP
            # is used to look up metadata and no metadata exists for this IP
            if '404 Not Found' not in e.output:
                failures.append(net_id)

    is_ok = len(failures) == 0
    metric_bool('neutron-metadata-agent-proxy_status', is_ok,
                m_name='maas_neutron')

    if is_ok:
        status_ok(m_name='maas_neutron')
    else:
        status_err('neutron metadata agent proxies fail on host %s '
                   'net_ids: %s' % (container, ','.join(failures)),
                   m_name='maas_neutron')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check neutron proxies')
    parser.add_argument('neutron_host',
                        type=str,
                        help='Neutron API hostname or IP address')
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
