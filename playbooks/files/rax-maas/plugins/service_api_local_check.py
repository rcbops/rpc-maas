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
from maas_common import status_ok
import requests
from requests import exceptions as exc


def check(args):
    headers = {'Content-type': 'application/json'}
    path_options = {}
    if args.auth:
        keystone = get_openstack_client('identity')
        auth_token = keystone.get_token()
        project_id = keystone.get_project_id()
        headers['auth_token'] = auth_token
        path_options['project_id'] = project_id

    scheme = args.ssl and 'https' or 'http'
    endpoint = '{scheme}://{ip}:{port}'.format(ip=args.ip, port=args.port,
                                               scheme=scheme)
    if args.version is not None:
        path_options['version'] = args.version
    path = args.path.format(path_options)

    s = requests.Session()
    s.headers.update(headers)

    short_name = args.name.split('_')[0]
    if path and not path.startswith('/'):
        url = '/'.join((endpoint, path))
    else:
        url = ''.join((endpoint, path))
    try:
        r = s.get(url, verify=False, timeout=180)
    except (exc.ConnectionError, exc.HTTPError, exc.Timeout):
        is_up = False
        metric_bool('client_success', False,
                    m_name='maas_{name}'.format(name=short_name))
    else:
        is_up = True
        metric_bool('client_success', True,
                    m_name='maas_{name}'.format(name=short_name))

    status_ok(m_name='maas_{name}'.format(name=short_name))
    metric_bool('{name}_api_local_status'.format(name=args.name), is_up)

    if is_up and r.ok:
        milliseconds = r.elapsed.total_seconds() * 1000
        metric('{name}_api_local_response_time'.format(name=args.name),
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check service is up.')
    parser.add_argument('name', help='Service name.')
    parser.add_argument('ip', type=ipaddr.IPv4Address,
                        help='Service IP address.')
    parser.add_argument('port', type=int, help='Service port.')
    parser.add_argument('--path', default='',
                        help='Service API path, this should include '
                             'placeholders for the version "{version}" and'
                             ' tenant ID "{tenant_id}" if required.')
    parser.add_argument('--auth', action='store_true', default=False,
                        help='Does this API check require auth?')
    parser.add_argument('--ssl', action='store_true', default=False,
                        help='Should SSL be used.')
    parser.add_argument('--version', help='Service API version.')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
