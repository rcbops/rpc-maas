#!/usr/bin/env python3

# Copyright 2023, Rackspace US, Inc.
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


def check(args):
    barbican = get_openstack_client('key_manager')

    try:
        local_endpoint = generate_local_endpoint(
            str(barbican.get_endpoint()), args.ip, args.port, args.protocol,
            '/secrets?limit=1000&offset=0'
        )
        resp = barbican.session.get(local_endpoint, timeout=180)

    except (exc.ConnectionError, exc.HTTPError, exc.Timeout):
        is_up = False
        metric_bool('client_success', False, m_name='maas_barbican')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_barbican')
        status_err(str(e), m_name='maas_barbican')
    else:
        is_up = resp.ok
        metric_bool('client_success', True, m_name='maas_barbican')
        milliseconds = resp.elapsed.total_seconds() * 1000
        secret_total = resp.json()['total']
        metric('barbican_secrets', 'uint32', secret_total)

    status_ok(m_name='maas_barbican')
    metric_bool('barbican_api_local_status', is_up, m_name='maas_barbican')
    # only want to send other metrics if api is up
    if is_up:
        metric('barbican_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Barbican API against local or remote address')
    parser.add_argument('ip', nargs='?',
                        type=ipaddr.IPv4Address,
                        help='Optional Barbican API server address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        default='9311',
                        help='Port for the Barbican API service')
    parser.add_argument('--protocol',
                        default='http',
                        help='Protocol used to contact the Barbican API service')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
