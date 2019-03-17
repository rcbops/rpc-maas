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

from maas_common import get_openstack_client
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from requests import exceptions as exc


def check(args):
    cinder = get_openstack_client('block_storage')
    volume_endpoint = '%s/os-services' % str(cinder.get_endpoint())

    try:
        # We cannot do /os-services?host=X as cinder returns a hostname of
        # X@lvm for cinder-volume binary
        resp = cinder.session.get(volume_endpoint, timeout=180)
    except (exc.ConnectionError, exc.HTTPError, exc.Timeout) as e:
        metric_bool('client_success', False, m_name='maas_cinder')
        status_err(str(e), m_name='maas_cinder')

    if not resp.ok:
        metric_bool('client_success', False, m_name='maas_cinder')
        status_err(
            'Could not get response from Cinder API',
            m_name='cinder'
        )
    else:
        metric_bool('client_success', True, m_name='maas_cinder')

    services = resp.json()['services']

    # We need to match against a host of X and X@lvm (or whatever backend)
    if args.host:
        backend = ''.join((args.host, '@'))
        services = [service for service in services
                    if (service['host'].startswith(backend) or
                        service['host'] == args.host)]

    if len(services) == 0:
        status_err(
            'No host(s) found in the service list',
            m_name='maas_cinder'
        )

    status_ok(m_name='maas_cinder')

    if args.host:
        for service in services:
            service_is_up = True
            name = '%s_status' % service['binary']

            if service['status'] == 'enabled' and service['state'] != 'up':
                service_is_up = False

            if '@' in service['host']:
                [host, backend] = service['host'].split('@')
                name = '%s-%s_status' % (service['binary'], backend)

            metric_bool(name, service_is_up)
    else:
        for service in services:
            service_is_up = True
            if service['status'] == 'enabled' and service['state'] != 'up':
                service_is_up = False

            name = '%s_on_host_%s' % (service['binary'], service['host'])
            metric_bool(name, service_is_up)


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Cinder API against"
                                     " local or remote address")
    parser.add_argument('hostname',
                        type=str,
                        help='Cinder API hostname or IP address')
    parser.add_argument('--host',
                        type=str,
                        help='Only return metrics for the specified host')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--protocol',
                        type=str,
                        default='http',
                        help='Protocol to use for cinder client')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
