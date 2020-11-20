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
import collections

import ipaddr
from maas_common import generate_local_endpoint
from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from requests import exceptions as exc

SERVER_STATUSES = ['ACTIVE', 'SHUTOFF', 'ERROR', 'PAUSED', 'SUSPENDED']


def check(args):
    nova = get_openstack_client('compute')

    try:
        local_endpoint = generate_local_endpoint(
            str(nova.get_endpoint()), args.ip, args.port, args.protocol,
            '/servers/detail?all_tenants=True'
        )
        resp = nova.session.get(local_endpoint, timeout=180)

    except (exc.ConnectionError, exc.HTTPError, exc.Timeout):
        is_up = False
        metric_bool('client_success', False, m_name='maas_nova')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_nova')
        status_err(str(e), m_name='maas_nova')
    else:
        is_up = resp.ok
        metric_bool('client_success', True, m_name='maas_nova')
        milliseconds = resp.elapsed.total_seconds() * 1000
        servers = resp.json()['servers']
        # gather some metrics
        status_count = collections.Counter(
            [s['status'] for s in servers]
        )

    status_ok(m_name='maas_nova')
    metric_bool('nova_api_local_status', is_up, m_name='maas_nova')
    # only want to send other metrics if api is up
    if is_up:
        metric('nova_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')
        for status in SERVER_STATUSES:
            metric('nova_instances_in_state_%s' % status,
                   'uint32',
                   status_count[status], 'instances')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Nova API against local or remote address')
    parser.add_argument('ip', nargs='?',
                        type=ipaddr.IPv4Address,
                        help='Optional Nova API server address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        default='8774',
                        help='Port for the nova API service')
    parser.add_argument('--protocol',
                        default='http',
                        help='Protocol used to contact the nova API service')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
