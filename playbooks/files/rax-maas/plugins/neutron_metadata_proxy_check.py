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
try:
    import lxc
    lxc_module_active = True
except ImportError:
    lxc_module_active = False
    pass
import shlex
import subprocess

from maas_common import get_openstack_client
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok

SERVICE_CHECK = 'ip netns exec %s curl -fvs 169.254.169.254:80'


def check(args):
    neutron = get_openstack_client('network')

    # Identify where the service check should be run
    try:
        container = []

        if lxc_module_active:
            all_containers = lxc.list_containers()
            for c in all_containers:
                if 'neutron_agents' in c:
                    container.append(c)
                    break
                elif 'neutron_server' in c:
                    container.append(c)
                    break

        if len(container) == 0:
            container = None
        else:
            container = container[0]

    except OSError:
        pass
    except IndexError:
        status_err('found no neutron agent or server containers',
                   m_name='maas_neutron')

    try:
        # Only check networks which have a port with DHCP enabled
        networks = [i.network_id for i in neutron.ports()
                    if i.device_owner == 'network:dhcp']

    # Not gathering API status metric, so catch any exception
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_neutron')
        status_err(str(e), m_name='maas_neutron')
    else:
        metric_bool('client_success', True, m_name='maas_neutron')

        # Iterate through each namespace and validate the metadata
        # service is responsive. A 404 from the request is typical as
        # the IP used for validation does not exist.
        failures = []
        for net in networks:
            namespace = 'qdhcp-%s' % net
            service_check_cmd = SERVICE_CHECK % namespace
            try:
                if container is None:
                    command = service_check_cmd
                    subprocess.check_output(command, shell=False,
                                            stderr=subprocess.STDOUT)
                elif lxc_module_active:
                    command = shlex.split('lxc-attach -n %s -- %s' % (
                        container,
                        service_check_cmd
                    ))
                    subprocess.check_output(command, shell=False,
                                            stderr=subprocess.STDOUT)

            except subprocess.CalledProcessError as e:
                # A HTTP 404 response is expected
                if '404 Not Found' not in e.output:
                    failures.append(net)

    is_ok = len(failures) == 0

    if is_ok:
        status_ok(m_name='maas_neutron')
        metric_bool('neutron-metadata-proxy_status', is_ok,
                    m_name='maas_neutron')
    else:
        metric_bool('neutron-metadata-proxy_status', is_ok,
                    m_name='maas_neutron')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check neutron'
                                     'metadata proxies.')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
