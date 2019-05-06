#!/usr/bin/env python

# Copyright 2017, Rackspace US, Inc.
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

import ipaddr
from maas_common import generate_local_endpoint
from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from requests import exceptions as exc


def check(args):
    octavia = get_openstack_client('load_balancer')

    try:
        if args.ip:
            octavia_local_endpoint = generate_local_endpoint(
                str(octavia.get_endpoint()), args.ip, args.port,
                args.protocol, '/lbaas/loadbalancers?limit=1'
            )
            resp = octavia.session.get(octavia_local_endpoint, timeout=180)

    except (exc.HTTPError, exc.Timeout, exc.ConnectionError):
        is_up = False
        metric_bool('client_success', False, m_name='maas_octavia')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_octavia')
        status_err(str(e), m_name='maas_octavia')
    else:
        is_up = resp.ok
        metric_bool('client_success', True, m_name='maas_octavia')
        milliseconds = resp.elapsed.total_seconds() * 1000

    status_ok(m_name='maas_octavia')
    metric_bool('octavia_api_local_status', is_up, m_name='maas_octavia')
    if is_up:
        # only want to send other metrics if api is up
        metric('octavia_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Octavia API against local or remote address')
    parser.add_argument('ip', nargs='?', type=ipaddr.IPv4Address,
                        help="Check Octavia API against "
                        " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        default='9876',
                        help='Port for the octavia service')
    parser.add_argument('--protocol',
                        default='http',
                        help='Protocol used to contact the octavia service')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
