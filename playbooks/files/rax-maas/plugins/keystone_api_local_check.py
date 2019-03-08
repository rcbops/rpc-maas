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

import ipaddr
from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
import requests.exceptions as exc


def check(args):
    keystone = get_openstack_client('identity')

    local_keystone_endpoint = "{}://{}:{}/v{}/services".format(
        args.protocol, args.ip, args.port,
        keystone.get_api_major_version()[0]
    )

    try:
        resp = keystone.session.get('%s' % local_keystone_endpoint,
                                    timeout=180)
        milliseconds = resp.elapsed.total_seconds() * 1000

        is_up = resp.ok
    except (exc.ConnectionError, exc.HTTPError, exc.Timeout):
        is_up = False
        metric_bool('client_success', False, m_name='maas_keystone')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_keystone')
        status_err(str(e), m_name='maas_keystone')
    else:
        metric_bool('client_success', True, m_name='maas_keystone')
        # gather some vaguely interesting metrics to return
        project_count = len([i for i in keystone.projects()])
        user_count = len([i for i in keystone.users()])

    status_ok(m_name='maas_keystone')
    metric_bool('keystone_api_local_status', is_up, m_name='maas_keystone')
    if is_up:
        metric('keystone_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')
        metric('keystone_user_count', 'uint32', user_count, 'users')
        metric('keystone_tenant_count', 'uint32', project_count, 'tenants')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Keystone API against local or remote address')
    parser.add_argument(
        'ip',
        nargs='?',
        type=ipaddr.IPv4Address,
        help='Check Keystone API against local or remote address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help='Protocol for keystone API')
    parser.add_argument('--port',
                        action='store',
                        default='5000',
                        help='Port for the keystone API service')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
