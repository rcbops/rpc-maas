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
from maas_common import get_auth_ref
from maas_common import get_keystone_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
import requests
from requests import exceptions as exc


def check(auth_ref, args):
    # We call get_keystone_client here as there is some logic within to get a
    # new token if previous one is bad.
    keystone = get_keystone_client(auth_ref)
    auth_token = keystone.auth_token
    registry_endpoint = '{protocol}://{ip}:{port}'.format(
        protocol=args.protocol,
        ip=args.ip,
        port=args.port
    )

    s = requests.Session()

    s.headers.update(
        {'Content-type': 'application/json',
         'x-auth-token': auth_token})

    try:
        # /images returns a list of public, non-deleted images
        r = s.get('%s/images' % registry_endpoint, verify=False, timeout=5)
        is_up = r.ok
    except (exc.ConnectionError, exc.HTTPError, exc.Timeout):
        is_up = False
        metric_bool('client_success', False, m_name='maas_glance')
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_glance')
        status_err(str(e), m_name='maas_glance')

    status_ok(m_name='maas_glance')
    metric_bool('client_success', True, m_name='maas_glance')
    metric_bool('glance_registry_local_status', is_up, m_name='maas_glance')
    # only want to send other metrics if api is up
    if is_up:
        milliseconds = r.elapsed.total_seconds() * 1000
        metric('glance_registry_local_response_time', 'double',
               '%.3f' % milliseconds, 'ms')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Glance Registry "
                                     " against local or remote address")
    parser.add_argument('ip', type=ipaddr.IPv4Address,
                        help='Glance Registry IP address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help='Protocol for the local glance registry API')
    parser.add_argument('--port',
                        action='store',
                        default='9191',
                        help='Port for local glance registry API')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
