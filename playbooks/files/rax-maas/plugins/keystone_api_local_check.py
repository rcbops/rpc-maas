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
from keystoneclient import exceptions as exc
from maas_common import get_keystone_client
from maas_common import get_os_component_major_api_version
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def check(args):
    identity_endpoint = '{protocol}://{ip}:{port}/'.format(
        protocol=args.protocol,
        port=args.port,
        ip=args.ip
    )
    auth_version = get_os_component_major_api_version('keystone')[0]
    if auth_version == 2:
        identity_endpoint += 'v2.0'
    else:
        identity_endpoint += 'v3'

    try:
        if args.ip:
            keystone = get_keystone_client(endpoint=identity_endpoint)
        else:
            keystone = get_keystone_client()

        is_up = True
    except (exc.HttpServerError, exc.ClientException):
        is_up = False
        metric_bool('client_success', False, m_name='maas_keystone')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_keystone')
        status_err(str(e), m_name='maas_keystone')
    else:
        metric_bool('client_success', True, m_name='maas_keystone')
        # time something arbitrary
        start = time.time()
        keystone.services.list()
        end = time.time()
        milliseconds = (end - start) * 1000

        # gather some vaguely interesting metrics to return
        if auth_version == 2:
            project_count = len(keystone.tenants.list())
            user_count = len(keystone.users.list())
        else:
            project_count = len(keystone.projects.list())
            user_count = len(keystone.users.list(domain='Default'))

    status_ok(m_name='maas_keystone')
    metric_bool('keystone_api_local_status', is_up, m_name='maas_keystone')
    # only want to send other metrics if api is up
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
