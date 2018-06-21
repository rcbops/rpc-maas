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
import datetime

import ipaddr
from maas_common import get_auth_ref
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
import requests


def check(auth_ref, args):
    if args.path:
        path = '/{path}'.format(path=args.path)
    else:
        path = ''
    endpoint = '{protocol}://{ip}:{port}{path}'.format(
        ip=args.ip,
        protocol=args.protocol,
        port=args.port,
        path=path
    )

    service_name = 'maas_mk8s_{service}'.format(service=args.service)

    try:
        if args.protocol.upper() == 'HTTPS':
            if args.certificate:
                verify = args.certificate
            else:
                verify = False
        else:
            verify = None

        # time something arbitrary
        start = datetime.datetime.now()
        r = requests.head(endpoint, verify=verify, allow_redirects=True)
        end = datetime.datetime.now()
        api_is_up = (r.status_code == 200)
    except (requests.HTTPError, requests.Timeout, requests.ConnectionError):
        api_is_up = False
        metric_bool('client_success', False, m_name=service_name)
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name=service_name)
        status_err(str(e), m_name=service_name)
    else:
        metric_bool('client_success', True, m_name=service_name)
        dt = (end - start)
        milliseconds = (dt.microseconds + dt.seconds * 10 ** 6) / 10 ** 3

    status_ok(m_name=service_name)
    metric_bool('managed_k8s_{service}_local_status'.format(
        service=args.service), api_is_up, m_name=service_name)
    if api_is_up:
        # only want to send other metrics if api is up
        metric('managed_k8s_{service}_local_response_time'.format(
            service=args.service),
            'double', '%.3f' % milliseconds, 'ms')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Managed K8S service against local or'
                    'remote address')
    parser.add_argument('ip', nargs='?', type=ipaddr.IPv4Address,
                        help="Check Check Managed K8S service against "
                        " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        default='8889',
                        help='Port for the managed k8s service')
    parser.add_argument('--protocol',
                        default='https',
                        help='Protocol used to contact the managed'
                             'k8s service')
    parser.add_argument('--certificate',
                        default=None,
                        help='Path to SSL certificate for managed'
                             'k8s service')
    parser.add_argument('--service',
                        default=None,
                        help='Name of the k8s service')
    parser.add_argument('--path',
                        default=None,
                        help='Path after the endpoint')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
